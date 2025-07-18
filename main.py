import logging
import os
import asyncio
import time
import subprocess
import uuid
import threading
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from groq import Groq
from dotenv import load_dotenv
from tts.piper_tts import PiperTTS
from signalwire.relay.consumer import Consumer
from signalwire.relay.calling import Call
from celery_worker.celery_app import celery_app
from urllib.parse import quote

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
# The TTS_ORCHESTRATOR_URL is now the service's own public URL,
# which we will get from the Render environment at runtime.
TTS_ORCHESTRATOR_URL = os.environ.get("RENDER_EXTERNAL_URL")

# --- Service Clients ---
groq_client = Groq(api_key=GROQ_API_KEY)
piper_tts_service = PiperTTS()

# --- Directory Setup ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created audio directory: {directory}")

app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

# --- TTS Generation Logic (from tts_orchestrator.py) ---
def cleanup_file(path: str):
    try:
        if os.path.exists(path): os.remove(path)
        logger.info(f"Cleaned up file: {path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {path}: {e}")

async def generate_tts_audio(text: str, background_tasks: BackgroundTasks) -> str:
    request_id = str(uuid.uuid4())
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    optimized_filename = f"{request_id}_optimized.wav"
    optimized_filepath = os.path.join(OPTIMIZED_AUDIO_DIR, optimized_filename)
    
    background_tasks.add_task(asyncio.sleep, 600)
    background_tasks.add_task(cleanup_file, raw_filepath)
    background_tasks.add_task(cleanup_file, optimized_filepath)

    generation_success = False
    if GROQ_API_KEY:
        try:
            logger.info(f"Attempting Groq TTS for text: '{text[:30]}...'")
            tts_start_time = time.monotonic()
            tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
            tts_response.write_to_file(raw_filepath)
            tts_end_time = time.monotonic()
            tts_latency = (tts_end_time - tts_start_time) * 1000
            logger.info(f"Groq TTS Latency: {tts_latency:.2f} ms")
            generation_success = True
        except Exception as e:
            logger.error(f"Groq TTS failed: {e}", exc_info=True)

    if not generation_success:
        try:
            logger.info("Attempting Piper TTS fallback.")
            if not piper_tts_service.model: await piper_tts_service.initialize()
            audio_bytes = await piper_tts_service.text_to_speech(text)
            if audio_bytes:
                with open(raw_filepath, "wb") as f: f.write(audio_bytes)
                generation_success = True
        except Exception as e:
            logger.error(f"Piper TTS fallback failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="All TTS providers failed.")

    ffmpeg_start_time = time.monotonic()
    command = ["ffmpeg", "-i", raw_filepath, "-ar", "8000", "-ac", "1", "-acodec", TELEPHONY_CODEC, "-y", optimized_filepath]
    process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"ffmpeg failed: {stderr.decode()}")
    ffmpeg_end_time = time.monotonic()
    ffmpeg_latency = (ffmpeg_end_time - ffmpeg_start_time) * 1000
    logger.info(f"ffmpeg Transcoding Latency: {ffmpeg_latency:.2f} ms")
        
    return optimized_filename

# --- SignalWire Relay Logic (from relay_server.py) ---
class VoiceAIAgent(Consumer):
    def setup(self):
        self.project = SIGNALWIRE_PROJECT_ID
        self.token = SIGNALWIRE_API_TOKEN
        self.contexts = [SIGNALWIRE_CONTEXT]
    
    async def ready(self):
        logger.info(f"✅ SignalWire Consumer ready on context '{SIGNALWIRE_CONTEXT}'")

    async def on_incoming_call(self, call: Call):
        logger.info(f"📞 Incoming call {call.id} from {call.from_number}.")
        await call.answer()
        asyncio.create_task(self.handle_conversation(call))

    async def handle_conversation(self, call: Call):
        logger.info(f"[{call.id}] Starting conversation.")
        try:
            # The play_tts_response function now returns a recording if a barge-in occurs.
            barge_in_recording = await self.play_tts_response(call, "Hello! Thank you for calling. How can I help you today?", use_groq_pipeline=False)
            
            recording_to_process = barge_in_recording

            while call.active:
                # If there was no barge-in on the last playback, we need to listen for the user's speech now.
                if not recording_to_process:
                    logger.info(f"[{call.id}] Listening for user input...")
                    recording_to_process = await call.record(beep=False, end_silence_timeout=0.8, record_format='wav')

                # If we have no recording from either barge-in or normal listening, loop again.
                if not recording_to_process or not recording_to_process.url:
                    logger.warning(f"[{call.id}] Recording was empty or failed.")
                    recording_to_process = None # Reset for the next loop
                    continue
                
                # We have a recording, send it to Celery.
                task = celery_app.send_task("get_llm_response_task", args=[call.id, recording_to_process.url])
                llm_response_text = task.get(timeout=15)
                
                # Reset for the next loop.
                recording_to_process = None

                if not llm_response_text:
                    logger.error(f"[{call.id}] Worker failed to produce LLM text.")
                    continue
                
                # Play the LLM response and listen for the next barge-in.
                recording_to_process = await self.play_tts_response(call, llm_response_text, use_groq_pipeline=True)
        except Exception as e:
            logger.error(f"[{call.id}] Unhandled exception in conversation: {e}", exc_info=True)
        finally:
            logger.info(f"[{call.id}] Conversation ended.")

    async def play_tts_response(self, call: Call, text: str, use_groq_pipeline: bool = True):
        logger.info(f"[{call.id}] Playing TTS for: '{text[:30]}...'. Using Groq Pipeline: {use_groq_pipeline}")
        
        play_finished_event = asyncio.Event()
        record_finished_event = asyncio.Event()

        async def on_play_finished(action):
            play_finished_event.set()

        async def on_record_finished(action):
            record_finished_event.set()

        try:
            call.on('play.finished', on_play_finished)
            call.on('play.error', on_play_finished)
            call.on('record.finished', on_record_finished)

            if use_groq_pipeline:
                background_tasks = BackgroundTasks()
                filename = await generate_tts_audio(text, background_tasks)
                final_audio_url = f"{TTS_ORCHESTRATOR_URL}/audio/{filename}"
                play_action = await call.play_audio_async(url=final_audio_url)
            else:
                play_action = await call.play_tts_async(text=text)

            record_action = await call.record_async(beep=False, end_silence_timeout=1.0)

            play_waiter = asyncio.create_task(play_finished_event.wait())
            record_waiter = asyncio.create_task(record_finished_event.wait())
            
            done, pending = await asyncio.wait([play_waiter, record_waiter], return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            if record_waiter in done:
                logger.info(f"[{call.id}] Barge-in detected. Stopping playback.")
                await play_action.stop()
                # Wait for the recording to complete and return the final result.
                return await record_action.completed
            else:
                logger.info(f"[{call.id}] Playback finished. Stopping listener.")
                await record_action.stop()
                return None

        except Exception as e:
            logger.error(f"[{call.id}] Failed to play TTS response: {e}", exc_info=True)
            await call.play_tts(text="I am sorry, a system error occurred.")
            return None
        finally:
            call.off('play.finished', on_play_finished)
            call.off('play.error', on_play_finished)
            call.off('record.finished', on_record_finished)

# --- FastAPI Endpoints and Startup Logic ---
@app.get("/generate-audio")
async def get_generated_audio_url(text: str, background_tasks: BackgroundTasks):
    if not text: raise HTTPException(status_code=400, detail="Text is required.")
    filename = await generate_tts_audio(text, background_tasks)
    return {"success": True, "filename": filename}

@app.get("/")
def read_root():
    return {"message": "Voice Agent Service is running."}

@app.on_event("startup")
def start_relay_consumer():
    # Verify all necessary environment variables are set before starting
    if not all([SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, TTS_ORCHESTRATOR_URL]):
        logger.critical("FATAL: Missing critical SignalWire or Render environment variables. The Relay Consumer will not start.")
        return
        
    def run_agent():
        # Create a new event loop for the new thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        agent = VoiceAIAgent()
        # The run() method is blocking, so it will run forever in this loop.
        agent.run()

    # Run the SignalWire consumer in a separate thread
    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()
    logger.info("SignalWire Relay Consumer started in a background thread.")
