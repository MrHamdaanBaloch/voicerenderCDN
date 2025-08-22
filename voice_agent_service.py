import os
import json
import base64
import logging
import asyncio
import wave
import audioop
import queue # Import the standard queue module
from typing import Optional, List

from fastapi import FastAPI, WebSocket, Request, Response, HTTPException
from starlette.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Start
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from groq import Groq
import redis

# -------------------------------
# Setup & Config
# -------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("VoiceAgentService")

app = FastAPI()

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
SIGNALWIRE_API_TOKEN = os.getenv("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_CONTEXT = os.getenv("SIGNALWIRE_CONTEXT")
SIGNALWIRE_PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_SPACE_URL = os.getenv("SIGNALWIRE_SPACE_URL")

if not DEEPGRAM_API_KEY:
    raise RuntimeError("DEEPGRAM_API_KEY is not set in .env file")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in .env file")
if not SIGNALWIRE_API_TOKEN:
    raise RuntimeError("SIGNALWIRE_API_TOKEN is not set in .env file")
if not SIGNALWIRE_PROJECT_ID:
    raise RuntimeError("SIGNALWIRE_PROJECT_ID is not set in .env file")
if not RENDER_EXTERNAL_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is not set in .env file. Required for SignalWire callbacks.")
# SIGNALWIRE_SPACE_URL and SIGNALWIRE_CONTEXT are often used but not strictly required for basic streaming
if not SIGNALWIRE_SPACE_URL:
    logger.warning("SIGNALWIRE_SPACE_URL is not set in .env file. This might be needed for some SignalWire operations.")
if not SIGNALWIRE_CONTEXT:
    logger.warning("SIGNALWIRE_CONTEXT is not set in .env file. This might be needed for some SignalWire operations.")

# Initialize clients
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

redis_client: Optional[redis.Redis] = (
    redis.from_url(REDIS_URL) if REDIS_URL else None
)

# Public dir to save converted WAVs for quick download
PUBLIC_AUDIO_DIR = "public_audio"
os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=PUBLIC_AUDIO_DIR), name="audio")

# Queue to hold transcripts for Groq processing (thread-safe for Deepgram thread)
transcript_queue = queue.Queue()

# -------------------------------
# Redis helpers (optional)
# -------------------------------
def _r_append(key: str, data: bytes) -> None:
    if not redis_client:
        return
    try:
        redis_client.append(key, data)
    except Exception as e:
        logger.exception(f"Redis append failed for {key}: {e}")

def _r_expire(key: str, seconds: int) -> None:
    if not redis_client:
        return
    try:
        redis_client.expire(key, seconds)
    except Exception as e:
        logger.exception(f"Redis expire failed for {key}: {e}")

def _r_get(key: str) -> Optional[bytes]:
    if not redis_client:
        return None
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.exception(f"Redis get failed for {key}: {e}")
        return None

# -------------------------------
# Deepgram Event Handlers
# -------------------------------
def on_deepgram_open(self, *args, **kwargs):
    logger.info(f"Deepgram OPEN")

def on_deepgram_transcript(self, result, **kwargs):
    try:
        alt = result.channel.alternatives[0]
        if alt.transcript:
            logger.info(f"📝 Deepgram Transcript: {alt.transcript}")
            # Put the transcript into the thread-safe queue
            transcript_queue.put(alt.transcript)
    except Exception as e:
        logger.error(f"Error processing Deepgram transcript: {e}")

def on_deepgram_error(self, error, **kwargs):
    logger.error(f"Deepgram ERROR: {error}")

def on_deepgram_close(self, *args, **kwargs):
    logger.info(f"Deepgram CLOSE")

# -------------------------------
# HTTP Routes
# -------------------------------
@app.get("/")
async def root():
    return {"message": "OK: Voice Agent Service up"}

@app.post("/incoming_call")
async def incoming_call(request: Request):
    """
    Respond with <Start><Stream> to route call audio to our WebSocket.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    frm = form.get("From", "N/A"); to = form.get("To", "N/A")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {frm}, To: {to}")

    if not RENDER_EXTERNAL_URL:
        raise HTTPException(status_code=503, detail="RENDER_EXTERNAL_URL not set")

    host = RENDER_EXTERNAL_URL.replace("https://", "").replace("http://", "")
    ws_url = f"wss://{host}/media/{call_sid}"

    vr = VoiceResponse()
    st = Start()
    st.stream(url=ws_url, track="both_tracks")  # request both; we forward 'inbound'
    vr.append(st)
    vr.pause(length=60)  # safety net to keep the call alive

    logger.info(f"[{call_sid}] Returning <Start><Stream> to {ws_url}")
    return Response(content=str(vr), media_type="application/xml")

@app.get("/save_audio/{call_sid}")
async def save_audio(call_sid: str):
    """
    Convert raw μ-law (8kHz) bytes in Redis to a mono 16-bit PCM WAV.
    """
    key = f"audio_dump:{call_sid}"
    raw = _r_get(key)
    if not raw:
        raise HTTPException(status_code=404, detail="No audio dump found (expired or missing).")

    try:
        pcm = audioop.ulaw2lin(raw, 2)  # -> 16-bit
        out_path = os.path.join(PUBLIC_AUDIO_DIR, f"{call_sid}.wav")
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm)
        logger.info(f"[{call_sid}] Saved WAV: {out_path} ({len(raw)} μ-law bytes)")
        return {"message": f"Saved to /audio/{call_sid}.wav"}
    except Exception as e:
        logger.exception(f"[{call_sid}] WAV conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert audio")

# -------------------------------
# WebSocket Route for SignalWire <Stream>
# -------------------------------
@app.websocket("/media/{call_sid}")
async def media_ws(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    logger.info(f"🎙️ WebSocket accepted for call {call_sid}")

    stream_sid: Optional[str] = None
    dump_key = f"audio_dump:{call_sid}"

    # prepare Redis key
    if redis_client:
        try:
            redis_client.delete(dump_key)
            logger.info(f"[{call_sid}] [AUDIO_DUMP] Initialized Redis key")
        except Exception as e:
            logger.exception(f"[{call_sid}] Redis init failed: {e}")

    # Deepgram live connection
    dg_conn = deepgram_client.listen.websocket.v("1")

    dg_conn.on(LiveTranscriptionEvents.Open, on_deepgram_open)
    dg_conn.on(LiveTranscriptionEvents.Transcript, on_deepgram_transcript)
    dg_conn.on(LiveTranscriptionEvents.Error, on_deepgram_error)
    dg_conn.on(LiveTranscriptionEvents.Close, on_deepgram_close)

    # Start Deepgram with μ-law / 8 kHz to match SignalWire media frames
    try:
        dg_conn.start(
            LiveOptions(
                model="nova-3",
                language="en-US",
                encoding="mulaw",    # SignalWire audio format
                sample_rate=8000,     # SignalWire audio format
                channels=1,
                smart_format=True,
                interim_results=False # Only get final transcripts
            )
        )
        logger.info(f"[{call_sid}] Deepgram START requested")
    except Exception as e:
        logger.exception(f"[{call_sid}] Failed to start Deepgram: {e}")
        dg_conn = None

    try:
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            event = msg.get("event")

            if event == "connected":
                logger.info(f"[{call_sid}] SignalWire connected. Protocol: {msg.get('protocol', 'N/A')}")

            elif event == "start":
                stream_sid = (msg.get("start") or {}).get("streamSid")
                logger.info(f"[{call_sid}] Stream START. SID: {stream_sid}")

            elif event == "media":
                media = msg.get("media", {})
                if media.get("track") != "inbound":
                    continue
                payload_b64 = media.get("payload")
                if not payload_b64:
                    continue

                try:
                    audio_bytes = base64.b64decode(payload_b64)
                except Exception:
                    logger.warning(f"[{call_sid}] Bad base64 payload; skipping")
                    continue

                # Optional dump
                _r_append(dump_key, audio_bytes)

                # Forward to Deepgram
                if dg_conn:
                    try:
                        dg_conn.send(audio_bytes)
                    except Exception as e:
                        logger.exception(f"[{call_sid}] Deepgram send failed: {e}")

            elif event == "stop":
                logger.info(f"[{call_sid}] Stream STOP")
                break

            else:
                logger.debug(f"[{call_sid}] Unknown event: {event}")

    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] WebSocket client disconnected")
    except Exception as e:
        logger.exception(f"[{call_sid}] WebSocket handler error: {e}")
    finally:
        _r_expire(dump_key, 3600)  # keep audio dump for 1 hour

        if dg_conn:
            try:
                await asyncio.sleep(1.0) # Give Deepgram more time to process final transcripts
                dg_conn.finish()
                logger.info(f"[{call_sid}] Deepgram FINISH")
            except Exception as e:
                logger.exception(f"[{call_sid}] Deepgram finish error: {e}")

        try:
            await websocket.close()
        except Exception:
            pass

        logger.info(f"[{call_sid}] WebSocket closed")

# -------------------------------
# Groq Processing Task
# -------------------------------
async def process_transcripts_with_groq():
    """
    Continuously pulls transcripts from the thread-safe queue and sends them to Groq.
    """
    logger.info("Groq processing task started.")
    while True:
        try:
            transcript = transcript_queue.get_nowait()
            if transcript is None: # Sentinel value to stop the task
                logger.info("Groq task: Received stop signal.")
                break

            logger.info(f"Sending to Groq: '{transcript}'")
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": transcript,
                        }
                    ],
                    model="llama3-8b-8192", # Or another suitable Groq model
                )
                groq_response = chat_completion.choices[0].message.content
                logger.info(f"🤖 Groq Response: {groq_response}\n")
            except Exception as e:
                logger.error(f"Error getting Groq response: {e}")
            finally:
                transcript_queue.task_done() # Mark as done even if Groq fails
        except queue.Empty:
            await asyncio.sleep(0.1) # Wait a bit if queue is empty
            continue
        except Exception as e:
            logger.error(f"Error in Groq processing task: {e}")

# -------------------------------
# Main Application Entry Point
# -------------------------------
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_transcripts_with_groq())
    logger.info("Voice Agent Service started.")

@app.on_event("shutdown")
async def shutdown_event():
    # Signal the Groq processing task to stop
    transcript_queue.put(None)
    logger.info("Voice Agent Service shutting down.")

if __name__ == "__main__":
    import uvicorn
    # Determine the port to run on. Use $PORT from environment (e.g., on Render) or default to 8000.
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting FastAPI application on port {port}. For local testing, ensure RENDER_EXTERNAL_URL is set to a public tunnel (e.g., ngrok) for SignalWire to connect. On Render, this will use the provided $PORT.")
    uvicorn.run(app, host="0.0.0.0", port=port)
