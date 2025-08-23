import os
import json
import base64
import logging
import asyncio
import wave
import audioop
import queue # Import the standard queue module
import time # Added for latency measurement
import aiofiles # Added for async file operations
import uuid # Added for unique IDs for temporary files
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
RAW_AUDIO_DIR = "temp_raw_audio" # Directory for temporary raw audio files
os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)
os.makedirs(RAW_AUDIO_DIR, exist_ok=True) # Ensure temp raw audio dir exists
app.mount("/audio", StaticFiles(directory=PUBLIC_AUDIO_DIR), name="audio")

# Queue to hold transcripts for Groq processing (thread-safe for Deepgram thread)
transcript_queue = queue.Queue()

# Dictionary to hold ongoing transcripts for each call_sid
call_transcript_buffers = {}

# Dictionary to hold WebSocket and stream_sid for each active call
call_state = {}

# -------------------------------
# TTS Logic & Helpers
# -------------------------------
def cleanup_file(path: str):
    """Safely removes a file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {path}: {e}")

async def generate_tts_mulaw_bytes_for_stream(text: str, call_sid: str) -> bytes:
    """Generates raw pcm_mulaw audio bytes suitable for a media stream."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{call_sid}] TTS Request [{request_id}]: Generating mu-law bytes for stream. Text: '{text[:50]}...'")
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    mulaw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_mulaw.raw")

    try:
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)

        command = [
            "ffmpeg", "-y", "-i", raw_filepath,
            "-ar", "8000", "-ac", "1",
            "-f", "mulaw", mulaw_filepath
        ]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f"ffmpeg mu-law conversion failed: {stderr.decode()}")

        async with aiofiles.open(mulaw_filepath, 'rb') as f:
            audio_bytes = await f.read()
        
        logger.info(f"[{call_sid}] TTS Request [{request_id}]: Successfully generated {len(audio_bytes)} bytes of mu-law audio.")
        return audio_bytes
    finally:
        cleanup_file(raw_filepath)
        cleanup_file(mulaw_filepath)

async def send_audio_payload_chunked(websocket: WebSocket, stream_sid: str, audio_bytes: bytes, frame_ms: int = 20, sample_rate: int = 8000, call_sid: str = None, user_is_speaking_event: asyncio.Event = None):
    """
    Send mu-law outbound audio to SignalWire as many small frames to mimic real-time.
    """
    bytes_per_ms = sample_rate // 1000
    frame_size = bytes_per_ms * frame_ms
    total = len(audio_bytes)
    pos = 0
    logger.info(f"[{call_sid}] [OUTBOUND_AUDIO] Starting to stream {total} bytes to SignalWire in {frame_size}-byte frames.")
    chunk_count = 0
    try:
        while pos < total:
            if user_is_speaking_event and user_is_speaking_event.is_set():
                logger.info(f"[{call_sid}] [BARGE-IN] User started speaking. Interrupting TTS playback.")
                break
            chunk_count += 1
            chunk = audio_bytes[pos:pos + frame_size]
            payload = base64.b64encode(chunk).decode("utf-8")
            media_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"track": "outbound", "payload": payload}
            }
            await websocket.send_text(json.dumps(media_message))
            pos += frame_size
            await asyncio.sleep(frame_ms / 1000.0)
        logger.info(f"[{call_sid}] [OUTBOUND_AUDIO] Finished streaming {chunk_count} chunks.")
    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] [OUTBOUND_AUDIO] Client disconnected during audio streaming. Halting.")
    except Exception as e:
        logger.exception(f"[{call_sid}] [OUTBOUND_AUDIO] Unexpected error while streaming outbound audio chunks: {e}")

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
    call_sid = kwargs.get('call_sid', 'unknown')
    logger.info(f"[{call_sid}] Deepgram OPEN")
    # Store start time for latency measurement
    kwargs['deepgram_start_time'] = time.time()

def on_deepgram_transcript(self, result, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    user_is_speaking_event = kwargs.get('user_is_speaking_event')
    try:
        if result.is_final:
            transcript = result.channel.alternatives[0].transcript
            if transcript:
                # Accumulate final transcripts into the buffer
                call_transcript_buffers.setdefault(call_sid, []).append(transcript)
                logger.info(f"[{call_sid}] 📝 Deepgram Final Transcript (accumulating): {transcript}")
                if user_is_speaking_event and transcript.strip():
                    user_is_speaking_event.set() # User is speaking, set event for barge-in
        else:
            # Log interim results for debugging, but don't process with LLM yet
            interim_transcript = result.channel.alternatives[0].transcript
            if interim_transcript:
                logger.debug(f"[{call_sid}] 📝 Deepgram Interim Transcript: {interim_transcript}")
    except Exception as e:
        logger.error(f"[{call_sid}] Error processing Deepgram transcript: {e}")

def on_deepgram_utterance_end(self, utterance_end, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    user_is_speaking_event = kwargs.get('user_is_speaking_event')
    if call_sid in call_transcript_buffers and call_transcript_buffers[call_sid]:
        full_utterance = " ".join(call_transcript_buffers[call_sid])
        logger.info(f"[{call_sid}] 🗣️ Utterance End Detected. Full utterance: '{full_utterance}'")
        
        # Measure latency from Deepgram start to utterance end
        deepgram_start_time = kwargs.get('deepgram_start_time')
        if deepgram_start_time:
            latency = (time.time() - deepgram_start_time) * 1000
            logger.info(f"[{call_sid}] ⏱️ Deepgram Utterance End Latency: {latency:.2f} ms")
        
        transcript_queue.put((full_utterance, time.time(), call_sid, user_is_speaking_event)) # Pass transcript, current time, call_sid, and event
        call_transcript_buffers[call_sid].clear() # Clear buffer after sending to Groq
    else:
        logger.debug(f"[{call_sid}] Utterance End detected but no accumulated transcript.")
    
    if user_is_speaking_event:
        user_is_speaking_event.clear() # User finished speaking, clear event

def on_deepgram_error(self, error, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    logger.error(f"[{call_sid}] Deepgram ERROR: {error}")

def on_deepgram_close(self, *args, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    logger.info(f"[{call_sid}] Deepgram CLOSE")

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
    user_is_speaking_event = asyncio.Event() # Event to signal if user is speaking (for barge-in)

    # Store websocket and user_is_speaking_event in call_state
    call_state[call_sid] = {"websocket": websocket, "user_is_speaking_event": user_is_speaking_event}

    # prepare Redis key
    if redis_client:
        try:
            redis_client.delete(dump_key)
            logger.info(f"[{call_sid}] [AUDIO_DUMP] Initialized Redis key")
        except Exception as e:
            logger.exception(f"[{call_sid}] Redis init failed: {e}")

    # Deepgram live connection
    dg_conn = deepgram_client.listen.websocket.v("1")

    # Pass call_sid, latency_tracking, and user_is_speaking_event to handlers using functools.partial
    from functools import partial
    latency_tracking = {} # Dictionary to store start times for this specific call's Deepgram connection
    dg_conn.on(LiveTranscriptionEvents.Open, partial(on_deepgram_open, call_sid=call_sid, latency_tracking=latency_tracking))
    dg_conn.on(LiveTranscriptionEvents.Transcript, partial(on_deepgram_transcript, call_sid=call_sid, latency_tracking=latency_tracking, user_is_speaking_event=user_is_speaking_event))
    dg_conn.on(LiveTranscriptionEvents.UtteranceEnd, partial(on_deepgram_utterance_end, call_sid=call_sid, latency_tracking=latency_tracking, user_is_speaking_event=user_is_speaking_event)) # New handler
    dg_conn.on(LiveTranscriptionEvents.Error, partial(on_deepgram_error, call_sid=call_sid, latency_tracking=latency_tracking))
    dg_conn.on(LiveTranscriptionEvents.Close, partial(on_deepgram_close, call_sid=call_sid, latency_tracking=latency_tracking))
    dg_conn.on(LiveTranscriptionEvents.SpeechStarted, partial(on_deepgram_speech_started, call_sid=call_sid, user_is_speaking_event=user_is_speaking_event)) # New handler for barge-in

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
                interim_results=True, # Enable interim results for better human-like interaction
                utterance_end_ms=1000, # Detect end of utterance after 1 second of silence
                punctuate=True # Enable punctuation for better LLM input
            )
        )
        logger.info(f"[{call_sid}] Deepgram START requested")
    except Exception as e:
        logger.exception(f"[{call_sid}] Failed to start Deepgram: {e}")
        dg_conn = None

    try:
        # Initial Greeting
        greeting_text = "Hello! Welcome to the voice agent. How can I help you today?"
        greeting_audio_bytes = await generate_tts_mulaw_bytes_for_stream(greeting_text, call_sid)

        # Wait for SignalWire 'start' event to get stream_sid before sending outbound audio
        while not stream_sid:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            event = msg.get("event")
            if event == "start":
                stream_sid = (msg.get("start") or {}).get("streamSid")
                call_state[call_sid]["stream_sid"] = stream_sid # Store stream_sid in call_state
                logger.info(f"[{call_sid}] Stream START. SID: {stream_sid}")
                break
            else:
                logger.debug(f"[{call_sid}] Received {event} while waiting for 'start' event.")

        if stream_sid:
            await send_audio_payload_chunked(websocket, stream_sid, greeting_audio_bytes, call_sid=call_sid, user_is_speaking_event=user_is_speaking_event)
        else:
            logger.error(f"[{call_sid}] Failed to get stream_sid, cannot play welcome message.")

        # Main loop to process incoming media from SignalWire
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            event = msg.get("event")

            if event == "connected":
                logger.info(f"[{call_sid}] SignalWire connected. Protocol: {msg.get('protocol', 'N/A')}")

            elif event == "start": # This should ideally only happen once, but handle defensively
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
    finally:
        # Clean up call state
        if call_sid in call_state:
            del call_state[call_sid]
            logger.info(f"[{call_sid}] Cleaned up call state.")

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
            transcript_data = transcript_queue.get_nowait()
            if transcript_data is None: # Sentinel value to stop the task
                logger.info("Groq task: Received stop signal.")
                break

            transcript, deepgram_utterance_end_time, call_sid, user_is_speaking_event = transcript_data
            
            # Measure latency from Deepgram utterance end to sending to Groq
            latency_to_groq_send = (time.time() - deepgram_utterance_end_time) * 1000
            logger.info(f"[{call_sid}] ⏱️ Latency (Utterance End to Groq Send): {latency_to_groq_send:.2f} ms")

            logger.info(f"[{call_sid}] Sending to Groq: '{transcript}'")
            groq_request_start_time = time.time()
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant. Respond concisely and naturally, like a human.",
                        },
                        {
                            "role": "user",
                            "content": transcript,
                        }
                    ],
                    model="llama3-8b-8192", # Or another suitable Groq model
                )
                groq_response_time = time.time()
                groq_response = chat_completion.choices[0].message.content
                
                # Measure Groq API latency
                groq_api_latency = (groq_response_time - groq_request_start_time) * 1000
                logger.info(f"[{call_sid}] ⏱️ Groq API Latency: {groq_api_latency:.2f} ms")
                logger.info(f"[{call_sid}] 🤖 Groq Response: {groq_response}\n")

                # Generate TTS for Groq response and send back to SignalWire
                tts_audio_bytes = await generate_tts_mulaw_bytes_for_stream(groq_response, call_sid)
                
                # Retrieve websocket and stream_sid from call_state
                current_call_state = call_state.get(call_sid)
                if current_call_state and current_call_state.get("websocket") and current_call_state.get("stream_sid"):
                    websocket_for_call = current_call_state["websocket"]
                    stream_sid_for_call = current_call_state["stream_sid"]
                    user_is_speaking_event_for_call = current_call_state["user_is_speaking_event"]
                    
                    await send_audio_payload_chunked(
                        websocket_for_call,
                        stream_sid_for_call,
                        tts_audio_bytes,
                        call_sid=call_sid,
                        user_is_speaking_event=user_is_speaking_event_for_call
                    )
                else:
                    logger.error(f"[{call_sid}] Cannot send outbound TTS: WebSocket or stream_sid not found in call_state.")

            except Exception as e:
                logger.error(f"[{call_sid}] Error getting Groq response or generating TTS: {e}")
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
