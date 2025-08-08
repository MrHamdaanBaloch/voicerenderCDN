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
from signalwire.voice_response import VoiceResponse, Connect, Stream
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

async def generate_tts_audio(text: str, background_tasks: BackgroundTasks) -> str:
    request_id = str(uuid.uuid4())
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    optimized_filename = f"{request_id}_optimized.wav"
    optimized_filepath = os.path.join(OPTIMIZED_AUDIO_DIR, optimized_filename)
    
    background_tasks.add_task(asyncio.sleep, 600)
    background_tasks.add_task(cleanup_file, raw_filepath)
    background_tasks.add_task(cleanup_file, optimized_filepath)

    try:
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)
    except Exception as e:
        logger.error(f"Groq TTS failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="TTS provider failed.")

    command = ["ffmpeg", "-i", raw_filepath, "-ar", "8000", "-ac", "1", "-acodec", TELEPHONY_CODEC, "-y", optimized_filepath]
    process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"ffmpeg failed: {stderr.decode()}")
        
    return optimized_filepath

def cleanup_file(path: str):
    try:
        if os.path.exists(path): os.remove(path)
    except Exception:
        pass

# --- FastAPI Endpoints (Bidirectional Streaming Architecture) ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    """Responds with cXML to start a bidirectional audio stream."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: Responding with cXML to start bidirectional stream.")
    
    response = VoiceResponse()
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    
    connect = Connect()
    connect.stream(url=websocket_url)
    response.append(connect)

    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional audio stream between SignalWire and Deepgram."""
    await websocket.accept()
    logger.info(f"🎙️ WebSocket connection established for call {call_sid}")

    dg_connection = deepgram_client.listen.asynclive.v("1")
    
    async def process_and_respond(transcript: str):
        logger.info(f"[{call_sid}] START processing transcript: '{transcript}'")
        redis_key = f"conversation:{call_sid}"
        try:
            history_json = redis_client.get(redis_key)
            conversation_history = json.loads(history_json) if history_json else []
            
            messages = [{"role": "system", "content": "You are a helpful and concise voice assistant."}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": transcript})

            chat_completion = await asyncio.to_thread(groq_client.chat.completions.create, messages=messages, model="llama3-8b-8192")
            llm_response_text = chat_completion.choices[0].message.content
            logger.info(f"[{call_sid}] LLM Response: '{llm_response_text}'")

            conversation_history.append({"role": "user", "content": transcript})
            conversation_history.append({"role": "assistant", "content": llm_response_text})
            redis_client.set(redis_key, json.dumps(conversation_history), ex=3600)

            if llm_response_text:
                background_tasks = BackgroundTasks()
                audio_filepath = await generate_tts_audio(llm_response_text, background_tasks)
                
                async with aiofiles.open(audio_filepath, 'rb') as f:
                    audio_bytes = await f.read()
                
                payload = base64.b64encode(audio_bytes).decode('utf-8')
                
                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "track": "outbound",
                        "payload": payload
                    }
                }
                await websocket.send_text(json.dumps(media_message))
                logger.info(f"[{call_sid}] Sent outbound audio ({len(audio_bytes)} bytes) to SignalWire.")

        except Exception as e:
            logger.error(f"[{call_sid}] Error in process_and_respond: {e}", exc_info=True)
        logger.info(f"[{call_sid}] END processing transcript")

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if transcript and result.speech_final:
            logger.info(f"[{call_sid}] Received speech_final transcript: '{transcript}'")
            asyncio.create_task(process_and_respond(transcript))
    
    async def on_error(self, error, **kwargs):
        logger.error(f"[{call_sid}] Deepgram error: {error}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    try:
        options = LiveOptions(model="nova-2-phonecall", language="en-US", encoding="mulaw", sample_rate=8000, punctuate=True, smart_format=True, interim_results=True, utterance_end_ms="1000", vad_events=True, endpointing=300)
        await dg_connection.start(options)
        logger.info(f"[{call_sid}] Successfully connected to Deepgram.")

        stream_sid = None
        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            event = message.get('event')
            
            if event == 'start':
                stream_sid = message['start']['streamSid']
                logger.info(f"[{call_sid}] Received start event from SignalWire. Stream SID: {stream_sid}")
                # Play welcome message
                asyncio.create_task(process_and_respond("Welcome"))
            elif event == 'media':
                payload = base64.b64decode(message['media']['payload'])
                if payload:
                    await dg_connection.send(payload)
            elif event == 'stop':
                logger.info(f"[{call_sid}] Received stop event from SignalWire. Closing connections.")
                break
            else:
                logger.warning(f"[{call_sid}] Received unknown event from SignalWire: {event}")
    
    except Exception as e:
        logger.error(f"[{call_sid}] Error in WebSocket handler: {e}", exc_info=True)
    finally:
        logger.info(f"[{call_sid}] Closing Deepgram connection.")
        await dg_connection.finish()
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
