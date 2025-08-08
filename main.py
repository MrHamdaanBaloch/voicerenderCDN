import logging
import os
import asyncio
import json
import random
import uuid
import base64
from fastapi import FastAPI, WebSocket, Response, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Connect, Stream, Play
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
import redis
import aiofiles

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
# Correctly configure keepalive at the client level
config = DeepgramClientOptions(keepalive="true")
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, config)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup & TTS Logic ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

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
            "ffmpeg", "-i", raw_filepath,
            "-ar", "8000", "-ac", "1",
            "-f", "mulaw", "-y", mulaw_filepath
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

async def delayed_cleanup(path: str, delay: int):
    """Waits for a delay then cleans up a file."""
    await asyncio.sleep(delay)
    cleanup_file(path)

async def send_audio_payload(websocket: WebSocket, stream_sid: str, audio_bytes: bytes):
    """Encodes and sends an audio payload over the WebSocket."""
    payload = base64.b64encode(audio_bytes).decode('utf-8')
    media_message = {
        "event": "media",
        "streamSid": stream_sid,
        "media": { "track": "outbound", "payload": payload }
    }
    await websocket.send_text(json.dumps(media_message))

# --- Application Startup Logic ---

# --- Application Startup Logic ---
# No startup tasks needed for this simplified architecture.

# --- FastAPI Endpoints (Decoupled Welcome Message Architecture) ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    """Responds with cXML to start a non-blocking stream with status callbacks, say a welcome message, and pause."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {body.get('From', 'N/A')}, To: {body.get('To', 'N/A')}")
    
    response = VoiceResponse()
    
    # 1. Start the media stream in the background with status callbacks for visibility
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    status_callback_url = f"{RENDER_EXTERNAL_URL}/stream_status"
    
    start = response.start()
    start.stream(url=websocket_url, status_callback=status_callback_url, status_callback_method="POST")
    logger.info(f"[{call_sid}] Enqueued <Start><Stream> to {websocket_url} with status callback to {status_callback_url}.")

    # 2. Immediately after, enqueue the welcome message
    welcome_text = "Welcome to the voice assistant. Please wait a moment while we connect you."
    response.say(welcome_text, voice="en-US-Standard-A")
    logger.info(f"[{call_sid}] Enqueued <Say> verb for welcome message.")

    # 3. Add a long pause to keep the call alive, allowing the stream to connect.
    response.pause(length=30)
    logger.info(f"[{call_sid}] Enqueued <Pause length=30> to prevent premature hangup.")
    
    logger.info(f"[{call_sid}] Responding with cXML for stabilized call handoff.")
    return Response(content=str(response), media_type="application/xml")

@app.post("/stream_status")
async def handle_stream_status(request: Request):
    """Receives and logs status updates for the WebSocket stream."""
    body = await request.form()
    call_sid = body.get("CallSid")
    stream_sid = body.get("StreamSid")
    event = body.get("StreamEvent")
    logger.info(f"STREAM STATUS [{call_sid}][{stream_sid}]: Event: {event}. Full data: {body}")
    return Response(status_code=200)

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional audio stream between SignalWire and Deepgram."""
    await websocket.accept()
    logger.info(f"🎙️ WebSocket connection established for call {call_sid}")

    dg_connection = deepgram_client.listen.asynclive.v("1")

    async def process_and_respond(transcript: str):
        logger.info(f"[{call_sid}] PROCESSING transcript: '{transcript}'")
        redis_key = f"conversation:{call_sid}"
        
        try:
            history_json = redis_client.get(redis_key)
            conversation_history = json.loads(history_json) if history_json else []
            
            system_prompt = (
                "You are a highly responsive, friendly, and human-like voice assistant. "
                "Keep your responses concise and conversational, suitable for a real-time phone call. "
                "Your goal is to provide accurate information quickly and naturally."
            )
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": transcript})
            
            logger.info(f"[{call_sid}] Sending transcript to LLM...")
            chat_completion = await asyncio.to_thread(groq_client.chat.completions.create, messages=messages, model="llama3-8b-8192")
            llm_response_text = chat_completion.choices[0].message.content
            logger.info(f"[{call_sid}] LLM generated response: '{llm_response_text[:50]}...'")

            conversation_history.append({"role": "user", "content": transcript})
            conversation_history.append({"role": "assistant", "content": llm_response_text})
            redis_client.set(redis_key, json.dumps(conversation_history), ex=3600)

            if llm_response_text:
                audio_bytes = await generate_tts_mulaw_bytes_for_stream(llm_response_text, call_sid)
                await send_audio_payload(websocket, stream_sid, audio_bytes)

        except Exception as e:
            logger.error(f"[{call_sid}] An error occurred in process_and_respond.", exc_info=True)
        
        logger.info(f"[{call_sid}] FINISHED processing transcript: '{transcript}'")

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript.strip()
        if transcript and result.speech_final:
            logger.info(f"[{call_sid}] Deepgram speech_final received: '{transcript}'")
            asyncio.create_task(process_and_respond(transcript))
    
    async def on_error(self, error, **kwargs):
        logger.error(f"[{call_sid}] Deepgram connection error: {error}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    stream_sid = None
    try:
        # Correctly pass options as keyword arguments
        await dg_connection.start(
            model="nova-2-phonecall",
            language="en-US",
            encoding="mulaw",
            sample_rate=8000,
            punctuate=True,
            smart_format=True,
            interim_results=False,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=600
        )
        logger.info(f"[{call_sid}] Successfully connected to Deepgram.")

        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            event = message.get('event')
            
            if event == 'start':
                stream_sid = message['start']['streamSid']
                logger.info(f"[{call_sid}] SignalWire stream started. SID: {stream_sid}")
            elif event == 'media':
                payload = base64.b64decode(message['media']['payload'])
                if payload:
                    await dg_connection.send(payload)
            elif event == 'stop':
                logger.info(f"[{call_sid}] SignalWire stream stopped. Closing connections.")
                break
            else:
                logger.warning(f"[{call_sid}] Received unknown event from SignalWire: {message}")
    
    except Exception as e:
        logger.error(f"[{call_sid}] CRITICAL ERROR in WebSocket handler: {e}", exc_info=True)
    finally:
        logger.info(f"[{call_sid}] Closing Deepgram connection.")
        await dg_connection.finish()
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
