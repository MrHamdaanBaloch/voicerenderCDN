import logging
import os
import asyncio
import json
import random
import uuid
import base64
from fastapi import FastAPI, WebSocket, Response, Request, BackgroundTasks, HTTPException
from starlette.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Connect, Stream, Play, Start
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
import redis
import aiofiles
import wave
import audioop

# --- Load Environment Variables & Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VoiceAgentService")

# --- FastAPI App Setup ---
app = FastAPI()

# --- Global Configuration & Clients ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_SPACE_URL = os.environ.get("SIGNALWIRE_SPACE_URL")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

TELEPHONY_CODEC = "pcm_mulaw"
OPTIMIZED_AUDIO_DIR = "public_audio"
RAW_AUDIO_DIR = "temp_raw_audio"

groq_client = Groq(api_key=GROQ_API_KEY)
# Correctly configure keepalive at the client level as per official documentation
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, config)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup & TTS Logic ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

@app.get("/debug_audio/{call_sid}")
async def get_debug_audio(call_sid: str):
    """Retrieves the raw inbound audio dump from Redis."""
    redis_key = f"audio_dump:{call_sid}"
    audio_bytes = redis_client.get(redis_key)
    if not audio_bytes:
        raise HTTPException(status_code=404, detail="Audio dump not found for this call SID.")
    
    logger.info(f"[{call_sid}] [AUDIO_DUMP] Serving {len(audio_bytes)} bytes of raw audio from Redis.")
    return Response(content=audio_bytes, media_type="application/octet-stream")

@app.get("/save_audio/{call_sid}")
async def save_audio(call_sid: str):
    """Retrieves the raw inbound audio dump from Redis and saves it to a file."""
    # Sanitize call_sid to remove any extraneous quotes from URL
    sanitized_call_sid = call_sid.strip('"\'')
    logger.info(f"[{sanitized_call_sid}] [AUDIO_DUMP] Received request to save audio.")
    redis_key = f"audio_dump:{sanitized_call_sid}"
    
    if not redis_client.exists(redis_key):
        logger.error(f"[{sanitized_call_sid}] [AUDIO_DUMP] Audio not found in Redis for key: {redis_key}")
        raise HTTPException(status_code=404, detail=f"Audio dump not found for call SID: {sanitized_call_sid}. It may have expired or never existed.")
        
    audio_bytes = redis_client.get(redis_key)
    logger.info(f"[{sanitized_call_sid}] [AUDIO_DUMP] Retrieved {len(audio_bytes)} bytes from Redis.")
    
    file_path = os.path.join(OPTIMIZED_AUDIO_DIR, f"{sanitized_call_sid}.wav")

    try:
        # Convert mu-law bytes to 16-bit linear PCM
        pcm_data = audioop.ulaw2lin(audio_bytes, 2)

        # Write the PCM data to a WAV file
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(1)       # mono
            wf.setsampwidth(2)       # 16-bit
            wf.setframerate(8000)    # 8kHz
            wf.writeframes(pcm_data)

        logger.info(f"[{sanitized_call_sid}] [AUDIO_DUMP] Saved {len(audio_bytes)} bytes of raw audio from Redis to {file_path}.")
        return {"message": f"Audio for call {sanitized_call_sid} saved to {file_path}."}
    except Exception as e:
        logger.error(f"[{sanitized_call_sid}] [AUDIO_DUMP] Failed to convert and save audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to convert audio: {str(e)}")

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

def cleanup_file(path: str):
    """Safely removes a file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {path}: {e}")

async def send_audio_payload_chunked(websocket: WebSocket, stream_sid: str, audio_bytes: bytes, frame_ms: int = 20, sample_rate: int = 8000, call_sid: str = None, user_is_speaking_event: asyncio.Event = None):
    """
    Send mu-law outbound audio to SignalWire as many small frames to mimic real-time.
    """
    bytes_per_ms = sample_rate // 1000
    frame_size = bytes_per_ms * frame_ms
    total = len(audio_bytes)
    pos = 0
    logger.info(f"[{call_sid}] [BLACKBOX] Starting to stream {total} bytes to SignalWire in {frame_size}-byte frames.")
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
        logger.info(f"[{call_sid}] [BLACKBOX] Finished streaming {chunk_count} chunks.")
    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] [BLACKBOX] Client disconnected during audio streaming. Halting.")
    except Exception as e:
        logger.exception(f"[{call_sid}] [BLACKBOX] Unexpected error while streaming outbound audio chunks: {e}")

# --- FastAPI Endpoints ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    """Responds with cXML to connect the call to our WebSocket for bidirectional streaming."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {body.get('From', 'N/A')}, To: {body.get('To', 'N/A')}")
    
    if not RENDER_EXTERNAL_URL:
        logger.critical("CRITICAL ERROR: RENDER_EXTERNAL_URL environment variable not set. Cannot process calls.")
        raise HTTPException(status_code=503, detail="Service Unavailable: Critical configuration is missing.")

    response = VoiceResponse()
    
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    
    start = Start()
    start.stream(url=websocket_url, track='both_tracks')
    response.append(start)

    # A long pause is crucial to keep the call alive while the WebSocket connects
    # and the agent takes control. The agent's logic will supersede this.
    response.pause(length=60)
    
    logger.info(f"[{call_sid}] Responding with resilient cXML (<Start><Stream>, <Pause>) to URL: {websocket_url}")
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional media stream for a call."""
    logger.info(f"!!!!!! WebSocket HANDLER ENTRY for call {call_sid}")
    await websocket.accept()
    logger.info(f"🎙️ [BLACKBOX] WebSocket connection accepted for call {call_sid}")

    # --- Initialize State & Events ---
    user_is_speaking_event = asyncio.Event()
    deepgram_ready = asyncio.Event()
    stream_sid = None
    dg_connection = None
    buffered_frames = []

    async def start_deepgram_connection():
        try:
            logger.info(f"[{call_sid}] [BLACKBOX] Attempting to start Deepgram connection...")
            dg_connection = deepgram_client.listen.asynclive.v("1")

            async def on_message(self, result, **kwargs):
                if result.channel.alternatives[0].transcript:
                    transcript = result.channel.alternatives[0].transcript
                    logger.info(f"[{call_sid}] [DEEPGRAM] Transcript received: {transcript}")

            async def on_open(self, open, **kwargs):
                logger.info(f"[{call_sid}] [BLACKBOX] Deepgram connection STARTED successfully.")
                deepgram_ready.set()
                logger.info(f"[{call_sid}] [BLACKBOX] Deepgram ready event SET.")
                # Flush any audio frames that were buffered before Deepgram was ready
                if buffered_frames:
                    logger.info(f"[{call_sid}] [BLACKBOX] Flushing {len(buffered_frames)} buffered frames to Deepgram.")
                    for frame in buffered_frames:
                        await dg_connection.send(frame)
                    buffered_frames.clear()
                    logger.info(f"[{call_sid}] [BLACKBOX] Buffer flushed. Deepgram startup task complete.")

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Open, on_open)

            await dg_connection.start(LiveOptions(model="nova-2-phonecall", language="en-US", encoding="mulaw", sample_rate=8000, smart_format=True))

        deepgram_task = asyncio.create_task(start_deepgram_connection())

        try:
            # Play a welcome message as soon as the stream starts to prevent dead air.
            await deepgram_ready.wait() # Wait until Deepgram is ready before we can potentially receive an interrupt.
            logger.info(f"[{call_sid}] [PROACTIVE_GREETING] Deepgram is ready. Generating and sending welcome message.")
            greeting_text = "Hello! Welcome to the voice agent. How can I help you today?"
            tts_audio_bytes = await generate_tts_mulaw_bytes_for_stream(greeting_text, call_sid)
            
            # We need the stream_sid to send audio, so we must wait for the 'start' event.
            # This creates a potential race condition if the 'start' event is delayed.
            # A more robust solution would queue this action until stream_sid is known.
        
            while not stream_sid:
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    data = json.loads(message)
                    if data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        logger.info(f"[{call_sid}] SignalWire stream started. SID: {stream_sid}")
                        break # Exit loop once we have the stream_sid
                except asyncio.TimeoutError:
                    logger.warning(f"[{call_sid}] Timed out waiting for 'start' event. Still waiting...")
                    continue
        
            if stream_sid:
                await send_audio_payload_chunked(websocket, stream_sid, tts_audio_bytes, call_sid=call_sid, user_is_speaking_event=user_is_speaking_event)
            else:
                logger.error(f"[{call_sid}] Failed to get stream_sid, cannot play welcome message.")
        
            # Main loop to process incoming media from SignalWire
            while True:
                message = await websocket.receive_text()
                logger.debug(f"[{call_sid}] [BLACKBOX] Received SignalWire message: {json.dumps(message)}")
                if event == 'connected':
                    logger.info(f"[{call_sid}] SignalWire WebSocket connected. Protocol: {message.get('protocol', 'N/A')}")
                elif event == 'start':
                    stream_sid = message['start'].get('streamSid') if message.get('start') else None
                    logger.info(f"[{call_sid}] SignalWire stream started. SID: {stream_sid}")

                    # Welcome message has been removed as per your request.
                    
                    # Feature: Audio Dumping for Debugging (now using Redis)
                    redis_key = f"audio_dump:{call_sid}"
                    redis_client.delete(redis_key) # Clear any previous dump for this SID
                    logger.info(f"[{call_sid}] [AUDIO_DUMP] Initialized Redis key for inbound audio dump: {redis_key}")

                elif event == 'media':
                    media = message.get('media', {})
                    track = media.get('track')
                    payload_b64 = media.get('payload')

                    if not payload_b64 or track != 'inbound':
                        continue
                    
                    # Decode the mu-law audio from base64
                    audio_bytes = base64.b64decode(payload_b64)

                    # Append to Redis for debugging
                    redis_client.append(f"audio_dump:{call_sid}", audio_bytes)

                    # Send audio to Deepgram
                    if dg_inbound_ready.is_set():
                        await dg_inbound.send(audio_bytes)
                    else:
                        inbound_buffer.append(audio_bytes)
                elif event == 'stop':
                    logger.info(f"[{call_sid}] SignalWire stream stopped. Closing connections.")
                    break
                else:
                    logger.warning(f"[{call_sid}] Received unknown event from SignalWire: {json.dumps(message)}")
            except WebSocketDisconnect:
                logger.info(f"[{call_sid}] SignalWire WebSocket disconnected gracefully.")
                break
            except Exception as e:
                logger.exception(f"[{call_sid}] CRITICAL ERROR in WebSocket handler main loop: {e}")
                break
    finally:
        # Set an expiry on the Redis audio dump key instead of closing a file
        redis_key = f"audio_dump:{call_sid}"
        if redis_client.exists(redis_key):
            redis_client.expire(redis_key, 3600) # Keep for 1 hour
            logger.info(f"[{call_sid}] [AUDIO_DUMP] Inbound audio dump in Redis set to expire in 1 hour.")

        logger.info(f"[{call_sid}] Cleaning up: finishing Deepgram connection.")
        try:
            await asyncio.sleep(0.1)
            await dg_inbound.finish()
        except Exception:
            logger.exception(f"[{call_sid}] Error while finishing Deepgram connection.")
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
