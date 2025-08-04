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
from signalwire.voice_response import VoiceResponse, Start, Stream
from signalwire.rest import Client as SignalwireRestClient
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import redis

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
THINKING_SOUNDS = ["hmm.wav", "umm.wav", "thinking.wav"]

groq_client = Groq(api_key=GROQ_API_KEY)
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# Initialize the SignalWire REST Client
# This is used to modify the call *after* it has been initiated.
sw_rest_client = SignalwireRestClient(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, signalwire_space_url=SIGNALWIRE_SPACE_URL)

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
        
    return optimized_filename

def cleanup_file(path: str):
    try:
        if os.path.exists(path): os.remove(path)
    except Exception:
        pass

# --- Core Voice Logic (Triggered by WebSocket) ---
async def process_transcript(call_sid: str, transcript: str):
    """Takes a transcript, gets an LLM response, and uses the REST API to play it back."""
    logger.info(f"[{call_sid}] Processing transcript: '{transcript}'")
    redis_key = f"conversation:{call_sid}"
    try:
        # Play a thinking sound using the REST API to modify the live call
        thinking_sound_url = f"{RENDER_EXTERNAL_URL}/audio/{random.choice(THINKING_SOUNDS)}"
        twiml_for_thinking = f'<Response><Play>{thinking_sound_url}</Play></Response>'
        sw_rest_client.calls(call_sid).update(twiml=twiml_for_thinking)

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
            filename = await generate_tts_audio(llm_response_text, background_tasks)
            final_audio_url = f"{RENDER_EXTERNAL_URL}/audio/{filename}"
            logger.info(f"[{call_sid}] Playing TTS response from URL: {final_audio_url}")
            
            # Use REST client to update the live call to play the new audio
            twiml_for_response = f'<Response><Play>{final_audio_url}</Play></Response>'
            sw_rest_client.calls(call_sid).update(twiml=twiml_for_response)

    except Exception as e:
        logger.error(f"[{call_sid}] Error in process_transcript: {e}", exc_info=True)

# --- FastAPI Endpoints (Pure Compatibility API Architecture) ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    """This is the webhook SignalWire calls. It responds with cXML to start the audio stream."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 Compatibility API received incoming call {call_sid}. Responding with cXML to start stream.")
    
    response = VoiceResponse()
    response.say("Hello! Please wait a moment while I connect you to the AI agent.")
    
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    
    # Use the <Start> and <Stream> verbs to start sending audio to our WebSocket,
    # following the official documentation's append pattern.
    start = Start()
    start.append(Stream(url=websocket_url))
    response.append(start)
    
    # This pause is crucial. It keeps the cXML document "running" and the call active
    # while the WebSocket is streaming. The conversation happens in the stream.
    response.pause(length=180) 

    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """This WebSocket endpoint receives audio from SignalWire and forwards it to Deepgram."""
    await websocket.accept()
    logger.info(f"🎙️ WebSocket connection established for call {call_sid}")

    try:
        dg_connection = deepgram_client.listen.asynclive.v("1")
        options = LiveOptions(model="nova-2-phonecall", language="en-US", encoding="mulaw", sample_rate=8000, punctuate=True, smart_format=True)
        await dg_connection.start(options)

        async def on_message(self, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if transcript and result.is_final:
                # When we get a final transcript, trigger the processing logic.
                asyncio.create_task(process_transcript(call_sid, transcript))

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            
            if message['event'] == 'media':
                payload = base64.b64decode(message['media']['payload'])
                await dg_connection.send(payload)
            elif message['event'] == 'stop':
                logger.info(f"[{call_sid}] Media stream stopped by SignalWire.")
                break
    
    except Exception as e:
        logger.error(f"[{call_sid}] Error in WebSocket handler: {e}", exc_info=True)
    finally:
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
