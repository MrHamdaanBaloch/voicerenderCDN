# main.py
import os
import json
import base64
import logging
import asyncio
import wave
import audioop
from typing import Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, HTTPException
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
    logger.warning("DEEPGRAM_API_KEY is not set. Live transcription will not start.")

# Deepgram client
deepgram = DeepgramClient(DEEPGRAM_API_KEY) if DEEPGRAM_API_KEY else None

# Redis (optional)
redis_client: Optional[redis.Redis] = redis.from_url(REDIS_URL) if REDIS_URL else None

# Storage for raw audio dumps (optional public mount just for convenience)
OPTIMIZED_AUDIO_DIR = "public_audio"
os.makedirs(OPTIMIZED_AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")


# -------------------------------
# Helpers
# -------------------------------
def _redis_append(key: str, data: bytes) -> None:
    if redis_client:
        try:
            redis_client.append(key, data)
        except Exception as e:
            logger.exception(f"Redis append failed for {key}: {e}")


def _redis_expire(key: str, seconds: int) -> None:
    if redis_client:
        try:
            redis_client.expire(key, seconds)
        except Exception as e:
            logger.exception(f"Redis expire failed for {key}: {e}")


def _redis_get(key: str) -> Optional[bytes]:
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
    return {"message": "Voice Agent Service is running and ready to receive calls."}


@app.post("/incoming_call")
async def incoming_call(request: Request):
    """
    Respond with cXML to start a WebSocket media stream to us.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    from_num = form.get("From", "N/A")
    to_num = form.get("To", "N/A")

    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {from_num}, To: {to_num}")

    if not RENDER_EXTERNAL_URL:
        logger.critical("RENDER_EXTERNAL_URL not set; cannot create WebSocket URL.")
        raise HTTPException(status_code=503, detail="Service Unavailable")

    # Build WebSocket URL for SignalWire to connect back
    # Ensure we provide a wss:// URL
    ws_host = RENDER_EXTERNAL_URL.replace("https://", "").replace("http://", "")
    websocket_url = f"wss://{ws_host}/media/{call_sid}"

    vr = VoiceResponse()
    start = Start()
    # Request both tracks so you *could* capture both sides; we only use inbound below.
    start.stream(url=websocket_url, track="both_tracks")
    vr.append(start)

    # Keep the call alive in case your app has a hiccup before taking over
    vr.pause(length=60)

    logger.info(f"[{call_sid}] Returning <Start><Stream> to {websocket_url}")
    return Response(content=str(vr), media_type="application/xml")


@app.get("/save_audio/{call_sid}")
async def save_audio(call_sid: str):
    """
    Convert the raw mu-law bytes stored in Redis for this call to a mono 8kHz 16-bit PCM WAV.
    """
    key = f"audio_dump:{call_sid}"
    audio_bytes = _redis_get(key)
    if not audio_bytes:
        raise HTTPException(status_code=404, detail="No audio dump found (may have expired).")

    # Convert Mu-law -> 16-bit linear PCM (mono, 8kHz)
    try:
        pcm = audioop.ulaw2lin(audio_bytes, 2)  # width=2 bytes (16-bit)
        out_path = os.path.join(OPTIMIZED_AUDIO_DIR, f"{call_sid}.wav")
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm)
        logger.info(f"[{call_sid}] Saved WAV to {out_path} ({len(audio_bytes)} mu-law bytes).")
        return {"message": f"Saved to {out_path}"}
    except Exception as e:
        logger.exception(f"[{call_sid}] WAV conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert audio.")


# -------------------------------
# WebSocket Route
# -------------------------------
@app.websocket("/media/{call_sid}")
async def media_ws(websocket: WebSocket, call_sid: str):
    """
    Handle SignalWire media streaming. We:
      - accept JSON messages
      - capture inbound mu-law audio frames
      - push them to Deepgram Live for transcription
      - optionally dump raw bytes to Redis for later inspection
    """
    await websocket.accept()
    logger.info(f"🎙️ WebSocket accepted for call {call_sid}")

    stream_sid: Optional[str] = None
    buffered_frames: List[bytes] = []
    deepgram_ready = asyncio.Event()
    dg_conn = None  # Deepgram connection instance

    # --- Setup Deepgram live connection if API key is present ---
    if deepgram:
        dg_conn = deepgram.listen.websocket.v("1")

        @dg_conn.on(LiveTranscriptionEvents.Open)
        def _on_open(_evt, **kwargs):
            logger.info(f"[{call_sid}] Deepgram WS OPEN")
            # Flush any buffered frames
            deepgram_ready.set()
            if buffered_frames:
                logger.info(f"[{call_sid}] Flushing {len(buffered_frames)} frames to Deepgram")
                for frame in buffered_frames:
                    try:
                        dg_conn.send(frame)
                    except Exception as e:
                        logger.exception(f"[{call_sid}] Failed sending buffered frame: {e}")
                buffered_frames.clear()

        @dg_conn.on(LiveTranscriptionEvents.Transcript)
        def _on_transcript(result, **kwargs):
            try:
                alt = result.channel.alternatives[0]
                if alt.transcript:
                    logger.info(f"[{call_sid}] ✍️ Transcript: {alt.transcript}")
            except Exception:
                # Be defensive; don’t let handler crash the app
                logger.debug(f"[{call_sid}] Received transcript event (no text)")

        @dg_conn.on(LiveTranscriptionEvents.Close)
        def _on_close(_evt, **kwargs):
            logger.info(f"[{call_sid}] Deepgram WS CLOSED")

        # Start Deepgram with mulaw/8k settings (SignalWire <Stream> media)
        # Note: channels=1 because we only forward 'inbound' track.
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
            logger.info(f"[{call_sid}] Deepgram connection START requested.")
        except Exception as e:
            logger.exception(f"[{call_sid}] Failed to start Deepgram connection: {e}")
            dg_conn = None
    else:
        logger.warning(f"[{call_sid}] Deepgram not configured; skipping transcription.")

    # Init Redis dump key (optional)
    dump_key = f"audio_dump:{call_sid}"
    if redis_client:
        try:
            redis_client.delete(dump_key)
            logger.info(f"[{call_sid}] [AUDIO_DUMP] Initialized Redis key {dump_key}")
        except Exception as e:
            logger.exception(f"[{call_sid}] Failed to init Redis key: {e}")

    # ---------------------------
    # Main receive loop
    # ---------------------------
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            event = data.get("event")

            if event == "connected":
                proto = data.get("protocol")
                logger.info(f"[{call_sid}] SignalWire connected. Protocol: {proto}")

            elif event == "start":
                stream_sid = data.get("start", {}).get("streamSid")
                logger.info(f"[{call_sid}] Stream START. SID: {stream_sid}")

            elif event == "media":
                media = data.get("media", {})
                track = media.get("track")
                payload_b64 = media.get("payload")
                if not payload_b64:
                    continue

                # Only forward inbound audio to Deepgram (mono)
                if track != "inbound":
                    continue

                # Decode base64 -> mu-law bytes
                try:
                    audio_bytes = base64.b64decode(payload_b64)
                except Exception:
                    logger.warning(f"[{call_sid}] Bad base64 payload; skipping frame.")
                    continue

                # Optional: dump raw mu-law bytes to Redis
                _redis_append(dump_key, audio_bytes)

                # Send to Deepgram (or buffer until ready)
                if dg_conn:
                    if deepgram_ready.is_set():
                        try:
                            dg_conn.send(audio_bytes)
                        except Exception as e:
                            logger.exception(f"[{call_sid}] Deepgram send failed: {e}")
                    else:
                        buffered_frames.append(audio_bytes)

            elif event == "stop":
                logger.info(f"[{call_sid}] Stream STOP received.")
                break

            else:
                logger.debug(f"[{call_sid}] Unknown event: {event}")

    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] Client disconnected.")
    except Exception as e:
        logger.exception(f"[{call_sid}] WebSocket handler error: {e}")
    finally:
        # Expire Redis dump
        _redis_expire(dump_key, 3600)  # keep for 1 hour

        # Close Deepgram cleanly
        if dg_conn:
            try:
                # Give Deepgram a breath to finish last frames
                await asyncio.sleep(0.1)
            except Exception:
                pass
            try:
                dg_conn.finish()
                logger.info(f"[{call_sid}] Deepgram connection finished.")
            except Exception as e:
                logger.exception(f"[{call_sid}] Error finishing Deepgram: {e}")

        try:
            await websocket.close()
        except Exception:
            pass

        logger.info(f"[{call_sid}] WebSocket closed.")
# main.py
import os
import json
import base64
import logging
import asyncio
import wave
import audioop
from typing import Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, HTTPException
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
    logger.warning("DEEPGRAM_API_KEY is not set. Live transcription will not start.")

# Deepgram client
deepgram = DeepgramClient(DEEPGRAM_API_KEY) if DEEPGRAM_API_KEY else None

# Redis (optional)
redis_client: Optional[redis.Redis] = redis.from_url(REDIS_URL) if REDIS_URL else None

# Storage for raw audio dumps (optional public mount just for convenience)
OPTIMIZED_AUDIO_DIR = "public_audio"
os.makedirs(OPTIMIZED_AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")


# -------------------------------
# Helpers
# -------------------------------
def _redis_append(key: str, data: bytes) -> None:
    if redis_client:
        try:
            redis_client.append(key, data)
        except Exception as e:
            logger.exception(f"Redis append failed for {key}: {e}")


def _redis_expire(key: str, seconds: int) -> None:
    if redis_client:
        try:
            redis_client.expire(key, seconds)
        except Exception as e:
            logger.exception(f"Redis expire failed for {key}: {e}")


def _redis_get(key: str) -> Optional[bytes]:
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
    return {"message": "Voice Agent Service is running and ready to receive calls."}


@app.post("/incoming_call")
async def incoming_call(request: Request):
    """
    Respond with cXML to start a WebSocket media stream to us.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    from_num = form.get("From", "N/A")
    to_num = form.get("To", "N/A")

    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {from_num}, To: {to_num}")

    if not RENDER_EXTERNAL_URL:
        logger.critical("RENDER_EXTERNAL_URL not set; cannot create WebSocket URL.")
        raise HTTPException(status_code=503, detail="Service Unavailable")

    # Build WebSocket URL for SignalWire to connect back
    # Ensure we provide a wss:// URL
    ws_host = RENDER_EXTERNAL_URL.replace("https://", "").replace("http://", "")
    websocket_url = f"wss://{ws_host}/media/{call_sid}"

    vr = VoiceResponse()
    start = Start()
    # Request both tracks so you *could* capture both sides; we only use inbound below.
    start.stream(url=websocket_url, track="both_tracks")
    vr.append(start)

    # Keep the call alive in case your app has a hiccup before taking over
    vr.pause(length=60)

    logger.info(f"[{call_sid}] Returning <Start><Stream> to {websocket_url}")
    return Response(content=str(vr), media_type="application/xml")


@app.get("/save_audio/{call_sid}")
async def save_audio(call_sid: str):
    """
    Convert the raw mu-law bytes stored in Redis for this call to a mono 8kHz 16-bit PCM WAV.
    """
    key = f"audio_dump:{call_sid}"
    audio_bytes = _redis_get(key)
    if not audio_bytes:
        raise HTTPException(status_code=404, detail="No audio dump found (may have expired).")

    # Convert Mu-law -> 16-bit linear PCM (mono, 8kHz)
    try:
        pcm = audioop.ulaw2lin(audio_bytes, 2)  # width=2 bytes (16-bit)
        out_path = os.path.join(OPTIMIZED_AUDIO_DIR, f"{call_sid}.wav")
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm)
        logger.info(f"[{call_sid}] Saved WAV to {out_path} ({len(audio_bytes)} mu-law bytes).")
        return {"message": f"Saved to {out_path}"}
    except Exception as e:
        logger.exception(f"[{call_sid}] WAV conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert audio.")


# -------------------------------
# WebSocket Route
# -------------------------------
@app.websocket("/media/{call_sid}")
async def media_ws(websocket: WebSocket, call_sid: str):
    """
    Handle SignalWire media streaming. We:
      - accept JSON messages
      - capture inbound mu-law audio frames
      - push them to Deepgram Live for transcription
      - optionally dump raw bytes to Redis for later inspection
    """
    await websocket.accept()
    logger.info(f"🎙️ WebSocket accepted for call {call_sid}")

    stream_sid: Optional[str] = None
    buffered_frames: List[bytes] = []
    deepgram_ready = asyncio.Event()
    dg_conn = None  # Deepgram connection instance

    # --- Setup Deepgram live connection if API key is present ---
    if deepgram:
        dg_conn = deepgram.listen.websocket.v("1")

        @dg_conn.on(LiveTranscriptionEvents.Open)
        def _on_open(_evt, **kwargs):
            logger.info(f"[{call_sid}] Deepgram WS OPEN")
            # Flush any buffered frames
            deepgram_ready.set()
            if buffered_frames:
                logger.info(f"[{call_sid}] Flushing {len(buffered_frames)} frames to Deepgram")
                for frame in buffered_frames:
                    try:
                        dg_conn.send(frame)
                    except Exception as e:
                        logger.exception(f"[{call_sid}] Failed sending buffered frame: {e}")
                buffered_frames.clear()

        @dg_conn.on(LiveTranscriptionEvents.Transcript)
        def _on_transcript(result, **kwargs):
            try:
                alt = result.channel.alternatives[0]
                if alt.transcript:
                    logger.info(f"[{call_sid}] ✍️ Transcript: {alt.transcript}")
            except Exception:
                # Be defensive; don’t let handler crash the app
                logger.debug(f"[{call_sid}] Received transcript event (no text)")

        @dg_conn.on(LiveTranscriptionEvents.Close)
        def _on_close(_evt, **kwargs):
            logger.info(f"[{call_sid}] Deepgram WS CLOSED")

        # Start Deepgram with mulaw/8k settings (SignalWire <Stream> media)
        # Note: channels=1 because we only forward 'inbound' track.
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
            logger.info(f"[{call_sid}] Deepgram connection START requested.")
        except Exception as e:
            logger.exception(f"[{call_sid}] Failed to start Deepgram connection: {e}")
            dg_conn = None
    else:
        logger.warning(f"[{call_sid}] Deepgram not configured; skipping transcription.")

    # Init Redis dump key (optional)
    dump_key = f"audio_dump:{call_sid}"
    if redis_client:
        try:
            redis_client.delete(dump_key)
            logger.info(f"[{call_sid}] [AUDIO_DUMP] Initialized Redis key {dump_key}")
        except Exception as e:
            logger.exception(f"[{call_sid}] Failed to init Redis key: {e}")

    # ---------------------------
    # Main receive loop
    # ---------------------------
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            event = data.get("event")

            if event == "connected":
                proto = data.get("protocol")
                logger.info(f"[{call_sid}] SignalWire connected. Protocol: {proto}")

            elif event == "start":
                stream_sid = data.get("start", {}).get("streamSid")
                logger.info(f"[{call_sid}] Stream START. SID: {stream_sid}")

            elif event == "media":
                media = data.get("media", {})
                track = media.get("track")
                payload_b64 = media.get("payload")
                if not payload_b64:
                    continue

                # Only forward inbound audio to Deepgram (mono)
                if track != "inbound":
                    continue

                # Decode base64 -> mu-law bytes
                try:
                    audio_bytes = base64.b64decode(payload_b64)
                except Exception:
                    logger.warning(f"[{call_sid}] Bad base64 payload; skipping frame.")
                    continue

                # Optional: dump raw mu-law bytes to Redis
                _redis_append(dump_key, audio_bytes)

                # Send to Deepgram (or buffer until ready)
                if dg_conn:
                    if deepgram_ready.is_set():
                        try:
                            dg_conn.send(audio_bytes)
                        except Exception as e:
                            logger.exception(f"[{call_sid}] Deepgram send failed: {e}")
                    else:
                        buffered_frames.append(audio_bytes)

            elif event == "stop":
                logger.info(f"[{call_sid}] Stream STOP received.")
                break

            else:
                logger.debug(f"[{call_sid}] Unknown event: {event}")

    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] Client disconnected.")
    except Exception as e:
        logger.exception(f"[{call_sid}] WebSocket handler error: {e}")
    finally:
        # Expire Redis dump
        _redis_expire(dump_key, 3600)  # keep for 1 hour

        # Close Deepgram cleanly
        if dg_conn:
            try:
                # Give Deepgram a breath to finish last frames
                await asyncio.sleep(0.1)
            except Exception:
                pass
            try:
                dg_conn.finish()
                logger.info(f"[{call_sid}] Deepgram connection finished.")
            except Exception as e:
                logger.exception(f"[{call_sid}] Error finishing Deepgram: {e}")

        try:
            await websocket.close()
        except Exception:
            pass

        logger.info(f"[{call_sid}] WebSocket closed.")
