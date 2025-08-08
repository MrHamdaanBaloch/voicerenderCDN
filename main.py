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
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, config)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup & TTS Logic ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

async def generate_tts_audio(text: str, call_sid: str) -> tuple[str, str]:
    """Generates TTS audio, returns raw and optimized file paths."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{call_sid}] TTS Request [{request_id}]: Generating audio for text: '{text[:50]}...'")
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    optimized_filename = f"{request_id}_optimized.wav"
    optimized_filepath = os.path.join(OPTIMIZED_AUDIO_DIR, optimized_filename)

    try:
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)
        logger.info(f"[{call_sid}] TTS Request [{request_id}]: Successfully received audio from Groq.")
    except Exception as e:
        logger.error(f"[{call_sid}] TTS Request [{request_id}]: Groq TTS API failed.", exc_info=True)
        raise

    command = [
        "ffmpeg", "-i", raw_filepath, 
        "-af", "aresample=resampler=soxr", # High-quality resampling
        "-ar", "8000", "-ac", "1", 
        "-acodec", TELEPHONY_CODEC, 
        "-y", optimized_filepath
    ]
    process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
    _, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_message = stderr.decode()
        logger.error(f"[{call_sid}] TTS Request [{request_id}]: ffmpeg conversion failed: {error_message}")
        cleanup_file(raw_filepath)
        raise Exception(f"ffmpeg failed: {error_message}")
    
    logger.info(f"[{call_sid}] TTS Request [{request_id}]: Successfully converted audio to {TELEPHONY_CODEC}.")
    return raw_filepath, optimized_filepath

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

@app.on_event("startup")
async def startup_event():
    """Tasks to run on application startup."""
    error_audio_path = os.path.join(OPTIMIZED_AUDIO_DIR, "error_message.wav")
    if not os.path.exists(error_audio_path):
        logger.info("Startup: Generating generic error message audio file...")
        try:
            error_text = "I'm sorry, I'm having a little trouble at the moment. Could you please say that again?"
            # Pass a dummy call_sid for logging purposes
            raw_path, optimized_path = await generate_tts_audio(error_text, "startup_task")
            os.rename(optimized_path, error_audio_path)
            cleanup_file(raw_path)
            logger.info("Startup: Successfully generated and saved error_message.wav.")
        except Exception as e:
            logger.error(f"Startup: Failed to generate error message audio: {e}", exc_info=True)

# --- FastAPI Endpoints (Decoupled Welcome Message Architecture) ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request, background_tasks: BackgroundTasks):
    """Plays a welcome message then starts a bidirectional audio stream."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {body.get('From', 'N/A')}, To: {body.get('To', 'N/A')}")
    
    response = VoiceResponse()
    
    try:
        logger.info(f"[{call_sid}] Generating welcome message audio.")
        welcome_text = "Welcome to the voice assistant. How can I help you today?"
        raw_path, optimized_path = await generate_tts_audio(welcome_text, call_sid)
        
        cleanup_file(raw_path)
        background_tasks.add_task(delayed_cleanup, optimized_path, 30)

        audio_url = f"{RENDER_EXTERNAL_URL}/audio/{os.path.basename(optimized_path)}"
        response.append(Play(url=audio_url))
        logger.info(f"[{call_sid}] Enqueued welcome message: {audio_url}")

    except Exception as e:
        logger.error(f"[{call_sid}] Failed to generate welcome message, responding with fallback.", exc_info=True)
        response.say("Sorry, we're having trouble connecting you right now. Please try again later.")

    # Connect to the WebSocket for the live conversation
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    connect = Connect()
    connect.stream(url=websocket_url)
    response.append(connect)
    
    logger.info(f"[{call_sid}] Responding with cXML to play welcome and then stream.")
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional audio stream between SignalWire and Deepgram."""
    await websocket.accept()
    logger.info(f"🎙️ WebSocket connection established for call {call_sid}")

    dg_connection = deepgram_client.listen.asynclive.v("1")
    
    stop_event = asyncio.Event()

    async def deepgram_keepalive(dg_connection):
        """Sends a keepalive message to Deepgram every 4 seconds."""
        while not stop_event.is_set():
            try:
                dg_connection.keepalive()
                logger.debug(f"[{call_sid}] Sent keepalive to Deepgram.")
                await asyncio.sleep(4)
            except Exception as e:
                logger.warning(f"[{call_sid}] Failed to send keepalive to Deepgram: {e}")
                break

    async def process_and_respond(transcript: str):
        logger.info(f"[{call_sid}] PROCESSING transcript: '{transcript}'")
        redis_key = f"conversation:{call_sid}"
        raw_audio_path, optimized_audio_path = None, None
        
        try:
            # 1. Retrieve conversation history from Redis
            logger.debug(f"[{call_sid}] Accessing Redis with key: {redis_key}")
            history_json = redis_client.get(redis_key)
            conversation_history = json.loads(history_json) if history_json else []
            logger.debug(f"[{call_sid}] Retrieved {len(conversation_history)} items from history.")
            
            # 2. Prepare and send request to Groq LLM
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

            # 3. Update conversation history in Redis
            conversation_history.append({"role": "user", "content": transcript})
            conversation_history.append({"role": "assistant", "content": llm_response_text})
            redis_client.set(redis_key, json.dumps(conversation_history), ex=3600)
            logger.debug(f"[{call_sid}] Updated conversation history in Redis.")

            # 4. Generate TTS audio and send to SignalWire
            if llm_response_text:
                raw_audio_path, optimized_audio_path = await generate_tts_audio(llm_response_text, call_sid)
                async with aiofiles.open(optimized_audio_path, 'rb') as f:
                    audio_bytes = await f.read()
                await send_audio_payload(websocket, stream_sid, audio_bytes)
                logger.info(f"[{call_sid}] Sent {len(audio_bytes)} bytes of audio to SignalWire.")

        except Exception as e:
            logger.error(f"[{call_sid}] An error occurred in process_and_respond.", exc_info=True)
            try:
                logger.info(f"[{call_sid}] Attempting to play fallback error message.")
                error_audio_path = os.path.join(OPTIMIZED_AUDIO_DIR, "error_message.wav")
                if os.path.exists(error_audio_path):
                    async with aiofiles.open(error_audio_path, 'rb') as f:
                        audio_bytes = await f.read()
                    await send_audio_payload(websocket, stream_sid, audio_bytes)
                    logger.info(f"[{call_sid}] Successfully sent fallback error message.")
            except Exception as fallback_e:
                logger.error(f"[{call_sid}] CRITICAL: Failed to send fallback error message.", exc_info=True)
        finally:
            # 5. Cleanup generated audio files
            if raw_audio_path: cleanup_file(raw_audio_path)
            if optimized_audio_path: asyncio.create_task(delayed_cleanup(optimized_audio_path, 600))
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

    try:
        options = LiveOptions(model="nova-2-phonecall", language="en-US", encoding="mulaw", sample_rate=8000, punctuate=True, smart_format=True, interim_results=False, utterance_end_ms="1000", vad_events=True, endpointing=600)
        logger.info(f"[{call_sid}] Connecting to Deepgram with options: {options}")
        await dg_connection.start(options)
        logger.info(f"[{call_sid}] Successfully connected to Deepgram.")

        keepalive_task = asyncio.create_task(deepgram_keepalive(dg_connection))
        stream_sid = None

        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            event = message.get('event')
            
            logger.debug(f"[{call_sid}] Received WebSocket message from SignalWire: {event}")

            if event == 'connected':
                logger.info(f"[{call_sid}] SignalWire WebSocket connected. Protocol: {message.get('protocol', 'N/A')}")
            elif event == 'start':
                stream_sid = message['start']['streamSid']
                logger.info(f"[{call_sid}] SignalWire stream started. SID: {stream_sid}")
            elif event == 'media':
                payload = base64.b64decode(message['media']['payload'])
                if payload:
                    # logger.debug(f"[{call_sid}] Relaying {len(payload)} bytes of media to Deepgram.")
                    await dg_connection.send(payload)
            elif event == 'stop':
                logger.info(f"[{call_sid}] SignalWire stream stopped. Closing connections.")
                break
            else:
                logger.warning(f"[{call_sid}] Received unknown event from SignalWire: {message}")
    
    except Exception as e:
        logger.error(f"[{call_sid}] Error in WebSocket handler: {e}", exc_info=True)
    finally:
        stop_event.set()
        if 'keepalive_task' in locals() and not keepalive_task.done():
            keepalive_task.cancel()
        logger.info(f"[{call_sid}] Closing Deepgram connection.")
        await dg_connection.finish()
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
