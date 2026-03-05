import logging
import os
import asyncio
import json
import uuid
import base64
import redis
import aiofiles
from fastapi import FastAPI, WebSocket, Response, Request, Depends, HTTPException
from starlette.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from groq import Groq
from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Start
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions

# --- Import Database Logic ---
from app.database import get_db
from app.models import User, Organization
from app.api.endpoints import router as api_router # Import the API router

# --- Load Environment Variables & Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VoiceAgentService")

# --- FastAPI App Setup ---
app = FastAPI()

# Include the API router
app.include_router(api_router)

# --- CORS Middleware (Fixed for Local Frontend & Preflight) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Configuration & Clients ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

TELEPHONY_CODEC = "pcm_mulaw"
OPTIMIZED_AUDIO_DIR = "public_audio"
RAW_AUDIO_DIR = "temp_raw_audio"

groq_client = Groq(api_key=GROQ_API_KEY)
dg_config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, dg_config)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

# --- Helper Functions ---

def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {path}: {e}")

async def generate_tts_mulaw_bytes_for_stream(text: str, call_sid: str) -> bytes:
    request_id = str(uuid.uuid4())
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    mulaw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_mulaw.raw")
    try:
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)
        command = ["ffmpeg", "-y", "-i", raw_filepath, "-ar", "8000", "-ac", "1", "-f", "mulaw", mulaw_filepath]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        async with aiofiles.open(mulaw_filepath, 'rb') as f:
            return await f.read()
    finally:
        cleanup_file(raw_filepath)
        cleanup_file(mulaw_filepath)

async def send_audio_payload_chunked(websocket: WebSocket, stream_sid: str, audio_bytes: bytes, frame_ms: int = 20, sample_rate: int = 8000, call_sid: str = None, user_is_speaking_event: asyncio.Event = None):
    bytes_per_ms = sample_rate // 1000
    frame_size = bytes_per_ms * frame_ms
    pos = 0
    try:
        while pos < len(audio_bytes):
            if user_is_speaking_event and user_is_speaking_event.is_set():
                break
            chunk = audio_bytes[pos:pos + frame_size]
            payload = base64.b64encode(chunk).decode("utf-8")
            await websocket.send_text(json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"track": "outbound", "payload": payload}
            }))
            pos += frame_size
            await asyncio.sleep(frame_ms / 1000.0)
    except Exception as e:
        logger.error(f"Error in streaming: {e}")

# --- API Endpoints ---

@app.get("/")
async def root():
    return {"status": "success", "message": "Voice Agent Service with Database is running."}
@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    body = await request.form()
    call_sid = body.get("CallSid")
    response = VoiceResponse()
    
    clean_url = RENDER_EXTERNAL_URL.replace('https://', '').replace('http://', '')
    websocket_url = f"wss://{clean_url}/media/{call_sid}"
    
    start = Start()
    start.stream(url=websocket_url, track='both_tracks')
    response.append(start)
    response.pause(length=60)
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    user_is_speaking_event = asyncio.Event()
    deepgram_ready = asyncio.Event()
    stream_sid = None
    dg_connection = None
    buffered_frames = []

    async def start_deepgram_connection():
        nonlocal dg_connection
        try:
            dg_connection = deepgram_client.listen.asynclive.v("1")

            async def on_message(self, result, **kwargs):
                if result.channel.alternatives[0].transcript:
                    logger.info(f"Transcript: {result.channel.alternatives[0].transcript}")

            async def on_open(self, open, **kwargs):
                deepgram_ready.set()
                if buffered_frames:
                    for frame in buffered_frames:
                        await dg_connection.send(frame)
                    buffered_frames.clear()

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Open, on_open)
            await dg_connection.start(LiveOptions(model="nova-2-phonecall", language="en-US", encoding="mulaw", sample_rate=8000))
        except Exception as e:
            logger.error(f"Deepgram error: {e}")

    deepgram_task = asyncio.create_task(start_deepgram_connection())

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get('event')

            if event == 'start':
                stream_sid = data['start']['streamSid']
                greeting_text = "Hello! Welcome to the voice agent."
                tts_audio = await generate_tts_mulaw_bytes_for_stream(greeting_text, call_sid)
                asyncio.create_task(send_audio_payload_chunked(websocket, stream_sid, tts_audio, call_sid=call_sid))

            elif event == 'media':
                media = data.get('media', {})
                if media.get('track') == 'inbound':
                    audio_bytes = base64.b64decode(media.get('payload'))
                    redis_client.append(f"audio_dump:{call_sid}", audio_bytes)
                    if deepgram_ready.is_set() and dg_connection:
                        await dg_connection.send(audio_bytes)
                    else:
                        buffered_frames.append(audio_bytes)
            elif event == 'stop':
                break
    except Exception as e:
        logger.error(f"WS Loop Error: {e}")
    finally:
        if dg_connection:
            await dg_connection.finish()
        deepgram_task.cancel()
        await websocket.close()
