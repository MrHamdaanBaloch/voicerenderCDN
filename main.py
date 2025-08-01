import logging
import os
import asyncio
import time
import subprocess
import uuid
import threading
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv
from signalwire.relay.consumer import Consumer
from signalwire.relay.calling import Call, ListenAIParams
from urllib.parse import quote
import redis
import json
import random

# --- Load Environment Variables & Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VoiceAgentService")

# --- FastAPI App Setup ---
app = FastAPI()

# --- Global Configuration ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEPHONY_CODEC = os.environ.get("TELEPHONY_CODEC", "pcm_mulaw")
OPTIMIZED_AUDIO_DIR = "public_audio"
RAW_AUDIO_DIR = "temp_raw_audio"
SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_CONTEXT = os.environ.get("SIGNALWIRE_CONTEXT", "voiceai")
TTS_ORCHESTRATOR_URL = os.environ.get("RENDER_EXTERNAL_URL")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

THINKING_SOUNDS = ["hmm.wav", "umm.wav", "thinking.wav"]

# --- Service Clients ---
groq_client = Groq(api_key=GROQ_API_KEY)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

# --- TTS Generation Logic (No changes needed here) ---
async def generate_tts_audio(text: str, background_tasks: BackgroundTasks) -> str:
    # ... [This function remains the same]
    request_id = str(uuid.uuid4())
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    optimized_filename = f"{request_id}_optimized.wav"
    optimized_filepath = os.path.join(OPTIMIZED_AUDIO_DIR, optimized_filename)
    
    background_tasks.add_task(asyncio.sleep, 600)
    background_tasks.add_task(cleanup_file, raw_filepath)
    background_tasks.add_task(cleanup_file, optimized_filepath)

    generation_success = False
    try:
        logger.info(f"Attempting Groq TTS for text: '{text[:30]}...'")
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)
        generation_success = True
    except Exception as e:
        logger.error(f"Groq TTS failed: {e}", exc_info=True)

    if not generation_success:
        # Fallback logic can be added here if needed
        raise HTTPException(status_code=500, detail="All TTS providers failed.")

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

# --- SignalWire Relay Logic ---
class VoiceAIAgent(Consumer):
    def setup(self):
        self.project = SIGNALWIRE_PROJECT_ID
        self.token = SIGNALWIRE_API_TOKEN
        self.contexts = [SIGNALWIRE_CONTEXT]
        self.active_calls = {}

    async def ready(self):
        logger.info(f"✅ SignalWire Consumer ready on context '{SIGNALWIRE_CONTEXT}'")

    async def on_incoming_call(self, call: Call):
        logger.info(f"📞 Incoming call {call.id} from {call.from_number}.")
        self.active_calls[call.id] = {
            "transcript_queue": asyncio.Queue(),
            "play_action": None
        }
        await call.answer()
        
        try:
            deepgram_options = {
                "model": "phonecall", "language": "en-US", "encoding": "mulaw",
                "sample_rate": 8000, "smart_format": True, "endpointing": 300
            }
            deepgram_url = f"wss://api.deepgram.com/v1/listen?{quote('&'.join([f'{k}={v}' for k, v in deepgram_options.items()]))}"

            ai_listener = await call.ai.listen(ListenAIParams(
                direction="both",
                post_url=deepgram_url,
                post_url_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
            ))
            ai_listener.on('message', lambda msg: self.on_ai_message(call, msg))
            
            asyncio.create_task(self.handle_conversation(call))
        except Exception as e:
            logger.error(f"[{call.id}] Error setting up AI listener: {e}", exc_info=True)
            await call.hangup()

    async def on_ai_message(self, call, message):
        if message.get('transcript') and message.get('is_final') and message.get('speech_final'):
            full_transcript = message['transcript'].strip()
            if full_transcript:
                logger.info(f"[{call.id}] Final Transcript: {full_transcript}")
                
                # This is the elegant barge-in. If we are playing audio, stop it.
                if self.active_calls[call.id]["play_action"]:
                    logger.info(f"[{call.id}] Barge-in detected. Stopping playback.")
                    await self.active_calls[call.id]["play_action"].stop()

                await self.active_calls[call.id]["transcript_queue"].put(full_transcript)

    async def handle_conversation(self, call: Call):
        logger.info(f"[{call.id}] Starting conversation.")
        redis_key = f"conversation:{call.id}"
        
        await self.play_tts_response(call, f"{TTS_ORCHESTRATOR_URL}/audio/welcome.wav")

        while call.active:
            try:
                logger.info(f"[{call.id}] Listening for user input...")
                user_transcript = await self.active_calls[call.id]["transcript_queue"].get()

                if not user_transcript: continue

                thinking_sound = random.choice(THINKING_SOUNDS)
                asyncio.create_task(call.play_audio(url=f"{TTS_ORCHESTRATOR_URL}/audio/{thinking_sound}"))
                
                history_json = redis_client.get(redis_key)
                conversation_history = json.loads(history_json) if history_json else []
                
                messages = [{"role": "system", "content": "You are a human-like voice assistant..."}]
                messages.extend(conversation_history)
                messages.append({"role": "user", "content": user_transcript})

                chat_completion = groq_client.chat.completions.create(messages=messages, model="llama3-8b-8192")
                llm_response_text = chat_completion.choices[0].message.content
                logger.info(f"[{call.id}] LLM Response: '{llm_response_text}'")

                conversation_history.append({"role": "assistant", "content": llm_response_text})
                redis_client.set(redis_key, json.dumps(conversation_history), ex=3600)

                if llm_response_text:
                    await self.play_tts_response(call, llm_response_text)

            except Exception as e:
                if not call.active: break
                logger.error(f"[{call.id}] Error in conversation loop: {e}", exc_info=True)
                await self.play_tts_response(call, "I'm sorry, a system error occurred.")
        
        logger.info(f"[{call.id}] Conversation ended.")
        del self.active_calls[call.id]

    async def play_tts_response(self, call: Call, text_or_url: str):
        logger.info(f"[{call.id}] Playing audio for: '{text_or_url[:50]}...'")
        try:
            if text_or_url.startswith("http"):
                final_audio_url = text_or_url
            else:
                background_tasks = BackgroundTasks()
                filename = await generate_tts_audio(text_or_url, background_tasks)
                final_audio_url = f"{TTS_ORCHESTRATOR_URL}/audio/{filename}"
            
            play_action = await call.play_audio_async(url=final_audio_url)
            self.active_calls[call.id]["play_action"] = play_action
            await play_action.completed()
        except Exception as e:
            logger.error(f"[{call.id}] Failed to play TTS response: {e}", exc_info=True)
        finally:
            if call.id in self.active_calls:
                self.active_calls[call.id]["play_action"] = None

# --- FastAPI Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Voice Agent Service is running."}

@app.on_event("startup")
def start_relay_consumer():
    if not all([SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, TTS_ORCHESTRATOR_URL, DEEPGRAM_API_KEY]):
        logger.critical("FATAL: Missing critical environment variables. The Relay Consumer will not start.")
        return
        
    thread = threading.Thread(target=VoiceAIAgent().run, daemon=True)
    thread.start()
    logger.info("SignalWire Relay Consumer started in a background thread.")
