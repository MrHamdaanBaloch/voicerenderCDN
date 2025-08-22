# main.py
import os
import json
import base64
import logging
import asyncio
import wave
import audioop
from typing import Optional, List

from fastapi import FastAPI, WebSocket, Request, Response, HTTPException
from starlette.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Start
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
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

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
REDIS_URL = os.environ.get("REDIS_URL")

if not DEEPGRAM_API_KEY:
    raise RuntimeError("DEEPGRAM_API_KEY is not set")

deepgram = DeepgramClient(DEEPGRAM_API_KEY)

redis_client: Optional[redis.Redis] = (
    redis.from_url(REDIS_URL) if REDIS_URL else None
)

# Public dir to save converted WAVs for quick download
PUBLIC_AUDIO_DIR = "public_audio"
os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=PUBLIC_AUDIO_DIR), name="audio")


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
    dg_conn = deepgram.listen.websocket.v("1")
    deepgram_ready = asyncio.Event()
    buffered_frames: List[bytes] = []

    # --- Handlers (register with .on(event, handler)) ---
    def on_open(_evt, **kwargs):
        logger.info(f"[{call_sid}] Deepgram OPEN")
        deepgram_ready.set()
        if buffered_frames:
            logger.info(f"[{call_sid}] Flushing {len(buffered_frames)} frames to Deepgram")
            for frame in buffered_frames:
                try:
                    dg_conn.send(frame)
                except Exception as e:
                    logger.exception(f"[{call_sid}] Deepgram send (buffered) failed: {e}")
            buffered_frames.clear()

    def on_transcript(result, **kwargs):
        try:
            alt = result.channel.alternatives[0]
            if alt.transcript:
                logger.info(f"[{call_sid}] 📝 {alt.transcript}")
        except Exception:
            logger.debug(f"[{call_sid}] Transcript event received (no text)")

    def on_close(_evt, **kwargs):
        logger.info(f"[{call_sid}] Deepgram CLOSE")

    dg_conn.on(LiveTranscriptionEvents.Open, on_open)
    dg_conn.on(LiveTranscriptionEvents.Transcript, on_transcript)
    dg_conn.on(LiveTranscriptionEvents.Close, on_close)

    # Start Deepgram with μ-law / 8 kHz to match SignalWire media frames
    try:
        dg_conn.start(
            LiveOptions(
                model="nova-3",
                language="en-US",
                encoding="mulaw",
                sample_rate=8000,
                channels=1,
                smart_format=True,
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
                    if deepgram_ready.is_set():
                        try:
                            dg_conn.send(audio_bytes)
                        except Exception as e:
                            logger.exception(f"[{call_sid}] Deepgram send failed: {e}")
                    else:
                        buffered_frames.append(audio_bytes)

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
                await asyncio.sleep(0.05)  # tiny grace period
            except Exception:
                pass
            try:
                dg_conn.finish()
                logger.info(f"[{call_sid}] Deepgram FINISH")
            except Exception as e:
                logger.exception(f"[{call_sid}] Deepgram finish error: {e}")

        try:
            await websocket.close()
        except Exception:
            pass

        logger.info(f"[{call_sid}] WebSocket closed")
