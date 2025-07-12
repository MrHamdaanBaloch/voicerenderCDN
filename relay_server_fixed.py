# /AIVOICE/relay_server_fixed.py (Decoupled & Resilient Final Version)
import logging
import sys
import os
import asyncio
import tempfile
import uuid
import aiohttp
from aiohttp import web
from dotenv import load_dotenv
from signalwire.relay.consumer import Consumer
from signalwire.relay.calling import Call, Play
import redis
import json

# --- HYPER-DETAILED LOGGING ---
log_file_handler = logging.FileHandler("relay_server.log", mode='w')
log_stream_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[log_file_handler, log_stream_handler])
logger = logging.getLogger(__name__)
logger.info("--- DECOUPLED & RESILIENT SCRIPT STARTED ---")

# --- SAFE IMPORTS (DECOUPLED) ---
try:
    # DECOUPLED: We import the Celery app instance, NOT the tasks themselves.
    from celery_worker.celery_app import celery_app
    logger.info("Successfully imported 'celery_worker.celery_app'.")
    from tts.piper_tts import PiperTTS
    logger.info("Successfully imported 'tts.piper_tts'.")
except ImportError as e:
    logger.critical(f"FATAL IMPORT ERROR: {e}", exc_info=True)
    sys.exit(1)

# --- Configuration ---
load_dotenv()
SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_CONTEXT = os.environ.get("SIGNALWIRE_CONTEXT", "voiceai")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_TTS_VOICE = os.environ.get("GROQ_TTS_VOICE", "Fritz-PlayAI")
PUBLIC_URL_BASE = os.environ.get("PUBLIC_URL_BASE")
AUDIO_SERVER_PORT = int(os.environ.get("AUDIO_SERVER_PORT", 8080))
logger.info("Environment variables loaded.")

# --- Service Clients ---
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    logger.info("Redis client connected.")
except Exception as e:
    logger.critical(f"FATAL: Could not connect to Redis: {e}", exc_info=True)
    sys.exit(1)

AUDIO_CACHE_DIR = tempfile.mkdtemp(prefix="auravoice_audio_")
logger.info(f"Audio cache created at: {AUDIO_CACHE_DIR}")

class VoiceAIAgent(Consumer):
    def setup(self):
        logger.info("Entering VoiceAIAgent.setup()")
        self.project = SIGNALWIRE_PROJECT_ID
        self.token = SIGNALWIRE_API_TOKEN
        self.contexts = [SIGNALWIRE_CONTEXT]
        self.tts_service = PiperTTS()
        self._processing_calls = set()
        # DO NOT initialize async tasks here. The event loop is not running yet.
        logger.info("Exiting VoiceAIAgent.setup()")

    async def ready(self):
        logger.info("Entering VoiceAIAgent.ready()")
        # The event loop is running now. This is the correct place for async initialization.
        asyncio.create_task(self.tts_service.initialize())
        asyncio.create_task(self._start_web_server())
        logger.info(f"✅ Consumer ready on context '{SIGNALWIRE_CONTEXT}'")
        logger.info("Exiting VoiceAIAgent.ready()")

    async def on_incoming_call(self, call: Call):
        logger.info(f"Entering on_incoming_call for call {call.id}")
        if call.id in self._processing_calls:
            logger.warning(f"[{call.id}] Ignoring duplicate event.")
            return
        
        self._processing_calls.add(call.id)
        logger.info(f"📞 Incoming call {call.id} from {call.from_number}. Locked.")
        
        try:
            answer_result = await call.answer()
            if answer_result.successful:
                logger.info(f"✅ Call {call.id} answered.")
                asyncio.create_task(self.handle_conversation(call))
            else:
                logger.error(f"❌ Failed to answer call {call.id}. Event: {answer_result.event}")
                self._processing_calls.remove(call.id)
        except Exception as e:
            logger.error(f"Error in on_incoming_call for {call.id}: {e}", exc_info=True)
            self._processing_calls.remove(call.id)

    async def handle_conversation(self, call: Call):
        logger.info(f"Entering handle_conversation for call {call.id}")
        session_id = str(uuid.uuid4())
        active_play = None
        try:
            redis_client.set(f"history:{call.id}", json.dumps([]))
            prompt_text = "Hello! I'm Aura, your AI assistant. How can I help you today?"

            while call.active:
                audio_url = await self._get_tts_audio_url(session_id, prompt_text)
                if not audio_url:
                    logger.error(f"[{call.id}] Could not generate TTS. Hanging up.")
                    await call.hangup()
                    break

                # Play audio asynchronously to allow for barge-in
                logger.info(f"[{call.id}] Playing audio asynchronously: {audio_url}")
                active_play = await call.play_audio_async(url=audio_url)
                
                # Record user's speech
                logger.info(f"[{call.id}] Starting recording to listen for user input...")
                record_result = await call.record(
                    beep=False,
                    end_silence_timeout=1.0,
                    terminators='#*' # Stop recording on these digits
                )

                # Stop any lingering playback once recording is done
                if active_play and not active_play.completed:
                    logger.info(f"[{call.id}] Stopping playback as recording is complete.")
                    await active_play.stop()

                if record_result.successful:
                    logger.info(f"[{call.id}] Recording complete. URL: {record_result.url}")
                    task = celery_app.send_task("process_recording_task", args=[call.id, record_result.url])
                    logger.info(f"[{call.id}] Dispatched Celery task {task.id} for processing.")
                    
                    try:
                        prompt_text = task.get(timeout=25.0) # Increased timeout for full pipeline
                        if not prompt_text:
                            prompt_text = "I'm sorry, I don't have a response for that."
                    except Exception as e:
                        logger.error(f"[{call.id}] Celery task failed or timed out: {e}", exc_info=True)
                        prompt_text = "I'm having a little trouble. Could you say that again?"
                else:
                    logger.warning(f"[{call.id}] Recording failed or timed out. Reason: {record_result.event}")
                    # If recording fails (e.g., user hangs up), break the loop.
                    break
        except Exception as e:
            logger.error(f"[{call.id}] Unhandled exception in conversation: {e}", exc_info=True)
        finally:
            if call.active:
                await call.hangup()
            logger.info(f"[{call.id}] Conversation ended. Unlocking.")
            self._processing_calls.remove(call.id)

    async def _get_tts_audio_url(self, session_id: str, text: str) -> str | None:
        logger.info(f"Entering _get_tts_audio_url for session {session_id}")
        audio_content, source_tts = None, None

        # 1. Attempt Groq TTS
        if GROQ_API_KEY:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            # Using a more standard model name as per recent API changes
            payload = {"model": "tts-1", "voice": GROQ_TTS_VOICE, "input": text, "response_format": "wav"}
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
                    async with s.post("https://api.groq.com/openai/v1/audio/speech", headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            audio_content = await resp.read()
                            source_tts = "Groq TTS"
                        else:
                            error_body = await resp.text()
                            logger.error(f"Groq TTS API failed: {resp.status} - {error_body}")
            except Exception as e:
                logger.error(f"Groq TTS request exception: {e}", exc_info=True)

        # 2. Fallback to PiperTTS
        if not audio_content and self.tts_service.model:
            logger.warning(f"[{session_id}] Groq TTS failed. Falling back to PiperTTS.")
            try:
                audio_content = await self.tts_service.text_to_speech(text)
                source_tts = "PiperTTS"
            except Exception as e:
                logger.error(f"[{session_id}] PiperTTS exception: {e}", exc_info=True)

        # 3. Serve the audio file
        if audio_content:
            logger.info(f"Generated audio using {source_tts}.")
            return self._serve_audio_file(session_id, audio_content)
        else:
            logger.error(f"All TTS providers failed for text: '{text[:50]}...'")
            return None

    def _serve_audio_file(self, session_id: str, audio_content: bytes) -> str | None:
        if not PUBLIC_URL_BASE: return None
        filename = f"{session_id}_{uuid.uuid4()}.wav"
        filepath = os.path.join(AUDIO_CACHE_DIR, filename)
        with open(filepath, "wb") as f: f.write(audio_content)
        return f"{PUBLIC_URL_BASE}/audio/{filename}"

    async def _start_web_server(self):
        app = web.Application()
        app.router.add_static('/audio', path=AUDIO_CACHE_DIR)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', AUDIO_SERVER_PORT)
        await site.start()
        logger.info(f"🔊 Audio web server started on http://0.0.0.0:{AUDIO_SERVER_PORT}")

    def teardown(self):
        logger.info("Consumer shutting down.")

if __name__ == "__main__":
    logger.info("Script __main__ block started.")
    if not all([SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, PUBLIC_URL_BASE]):
        logger.critical("FATAL: Missing critical environment variables.")
    else:
        try:
            agent = VoiceAIAgent()
            agent.run()
        except Exception as e:
            logger.critical(f"FATAL: Unhandled exception in agent.run(): {e}", exc_info=True)
    logger.info("Script __main__ block finished.")
