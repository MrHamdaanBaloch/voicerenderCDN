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
from signalwire.rest import Client as SignalwireRestClient
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
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
# Configure Deepgram client with keepalive option per official documentation
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, config)
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
    logger.info(f"[{call_sid}] START process_transcript for transcript: '{transcript}'")
    redis_key = f"conversation:{call_sid}"
    try:
        # Play a thinking sound using the REST API to modify the live call
        thinking_sound_url = f"{RENDER_EXTERNAL_URL}/audio/{random.choice(THINKING_SOUNDS)}"
        twiml_for_thinking = f'<Response><Play>{thinking_sound_url}</Play></Response>'
        logger.info(f"[{call_sid}] Sending TwiML for thinking sound: {twiml_for_thinking}")
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
            logger.info(f"[{call_sid}] Sending TwiML for LLM response: {twiml_for_response}")
            sw_rest_client.calls(call_sid).update(twiml=twiml_for_response)

    except Exception as e:
        logger.error(f"[{call_sid}] Error in process_transcript: {e}", exc_info=True)
    logger.info(f"[{call_sid}] END process_transcript")

# --- FastAPI Endpoints (Pure Compatibility API Architecture) ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    """This is the webhook SignalWire calls. It responds with cXML to start the audio stream."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: Received request from SignalWire. Body: {body}")
    
    response = VoiceResponse()
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    
    # Use <Connect><Stream/></Connect> for a bidirectional stream per official docs.
    # This is a blocking verb that holds the call open for the duration of the stream.
    connect = Connect()
    connect.stream(url=websocket_url)
    response.append(connect)

    logger.info(f"[{call_sid}] Responding with cXML to start bidirectional stream: {str(response)}")
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """This WebSocket endpoint receives audio from SignalWire and forwards it to Deepgram."""
    await websocket.accept()
    logger.info(f"🎙️ WebSocket connection established for call {call_sid}")

    try:
        dg_connection = deepgram_client.listen.asynclive.v("1")

        async def on_message(self, result, **kwargs):
            logger.debug(f"[{call_sid}] Deepgram on_message triggered.")
            transcript = result.channel.alternatives[0].transcript
            if transcript and result.speech_final:
                logger.info(f"[{call_sid}] Received speech_final transcript: '{transcript}'")
                asyncio.create_task(process_transcript(call_sid, transcript))
        
        async def on_error(self, error, **kwargs):
            logger.error(f"[{call_sid}] Deepgram on_error triggered: {error}")

        async def on_speech_started(self, speech_started, **kwargs):
            logger.info(f"[{call_sid}] Deepgram on_speech_started triggered: {speech_started}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)

        options = LiveOptions(
            model="nova-2-phonecall",
            language="en-US",
            encoding="mulaw",
            sample_rate=8000,
            punctuate=True,
            smart_format=True,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300
        )
        await dg_connection.start(options)
        logger.info(f"[{call_sid}] Successfully connected to Deepgram with advanced options.")

        while True:
            message_str = await websocket.receive_text()
            logger.debug(f"[{call_sid}] Raw WS message from SignalWire: {message_str[:250]}...")
            message = json.loads(message_str)
            event = message.get('event')
            
            if event == 'media':
                payload = base64.b64decode(message['media']['payload'])
                if payload:
                    logger.info(f"[{call_sid}] Relaying audio payload of size {len(payload)} to Deepgram.")
                    await dg_connection.send(payload)
                else:
                    logger.warning(f"[{call_sid}] Received empty media payload.")
            elif event == 'start':
                logger.info(f"[{call_sid}] Received start event from SignalWire: {message}")
                # Now that the stream is confirmed, play the welcome message via REST API
                try:
                    welcome_message = "Hello! How can I help you today?"
                    twiml_for_welcome = f'<Response><Say voice="Polly.Joanna-Neural">{welcome_message}</Say></Response>'
                    logger.info(f"[{call_sid}] Sending TwiML for welcome message: {twiml_for_welcome}")
                    sw_rest_client.calls(call_sid).update(twiml=twiml_for_welcome)
                except Exception as e:
                    logger.error(f"[{call_sid}] Error playing welcome message: {e}")
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
