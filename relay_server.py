import logging
import asyncio
import os
import sys
import tempfile
import uuid
import aiohttp
from aiohttp import web
from dotenv import load_dotenv
import redis
import json
import time
from urllib.parse import quote

# --- Load Environment Variables ---
load_dotenv()

# --- Imports and Config ---
from signalwire.relay.consumer import Consumer
from signalwire.relay.calling import Call
from celery_worker.celery_app import celery_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AuraVoice")

SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_CONTEXT = os.environ.get("SIGNALWIRE_CONTEXT", "voiceai")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
# This will now be the URL provided by Render for your TTS orchestrator
TTS_ORCHESTRATOR_URL = os.environ.get("TTS_ORCHESTRATOR_URL")

# --- Service Clients ---
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis client connected.")
except Exception as e:
    logger.critical(f"FATAL: Could not connect to Redis: {e}", exc_info=True)
    sys.exit(1)

class VoiceAIAgent(Consumer):
    def setup(self):
        self.project = SIGNALWIRE_PROJECT_ID
        self.token = SIGNALWIRE_API_TOKEN
        self.contexts = [SIGNALWIRE_CONTEXT]
        self._processing_calls = set()

    async def ready(self):
        logger.info(f"✅ Consumer ready on context '{SIGNALWIRE_CONTEXT}'")

    async def on_incoming_call(self, call: Call):
        if call.id in self._processing_calls:
            return
        self._processing_calls.add(call.id)
        logger.info(f"📞 Incoming call {call.id} from {call.from_number}.")
        try:
            await call.answer()
            asyncio.create_task(self.handle_conversation(call))
        except Exception as e:
            logger.error(f"Error in on_incoming_call for {call.id}: {e}", exc_info=True)
            self._processing_calls.remove(call.id)

    async def handle_conversation(self, call: Call):
        logger.info(f"[{call.id}] Starting conversation.")
        try:
            # Dynamically generate the welcome message using our robust, ffmpeg-powered TTS pipeline.
            # This is the most reliable method and ensures perfect audio quality.
            await self.play_tts_response(call, "Hello! Thank you for calling. How can I help you today?")

            while call.active:
                logger.info(f"[{call.id}] Listening for user input...")
                record_action = await call.record(beep=False, end_silence_timeout=0.8, record_format='wav')
                
                if not record_action.url:
                    logger.warning(f"[{call.id}] Recording was empty or failed.")
                    continue

                logger.info(f"[{call.id}] Recording complete. Getting LLM response from worker.")
                task = celery_app.send_task("get_llm_response_task", args=[call.id, record_action.url])
                llm_response_text = task.get(timeout=15) # Wait for the LLM result

                if not llm_response_text:
                    logger.error(f"[{call.id}] Worker failed to produce LLM text.")
                    continue

                logger.info(f"[{call.id}] Received LLM response: '{llm_response_text[:50]}...'")
                await self.play_tts_response(call, llm_response_text)
        
        except Exception as e:
            logger.error(f"[{call.id}] Unhandled exception in conversation: {e}", exc_info=True)
        finally:
            logger.info(f"[{call.id}] Conversation ended.")
            self._processing_calls.remove(call.id)

    async def play_tts_response(self, call: Call, text: str):
        """Calls the TTS orchestrator to get a playable URL and plays it on the call."""
        logger.info(f"[{call.id}] Entering play_tts_response for text: '{text[:30]}...'")
        try:
            encoded_text = quote(text)
            generation_url = f"{TTS_ORCHESTRATOR_URL}/generate-audio?text={encoded_text}"
            
            logger.info(f"[{call.id}] Step 1: Requesting audio from orchestrator: {generation_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(generation_url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"TTS orchestrator returned an error: {response.status} - {error_text}")
                        raise Exception("TTS orchestrator failed.")
                    
                    response_json = await response.json()
                    filename = response_json.get("filename")

            if not filename:
                raise Exception("TTS orchestrator did not return a valid filename.")

            final_audio_url = f"{TTS_ORCHESTRATOR_URL}/audio/{filename}"
            logger.info(f"[{call.id}] Step 2: Successfully got audio URL: {final_audio_url}")
            
            # Implement barge-in logic
            logger.info(f"[{call.id}] Step 3: Initiating playback and concurrent recording (barge-in).")
            play_action = await call.play_audio_async(url=final_audio_url)
            listen_action = await call.record_async(beep=False, end_silence_timeout=1.0)
            
            await asyncio.wait(
                [play_action.wait_for_completed(), listen_action.wait_for_completed()],
                return_when=asyncio.FIRST_COMPLETED
            )

            if listen_action.completed:
                logger.info(f"[{call.id}] Barge-in detected! Stopping playback.")
                await play_action.stop()
            else:
                await listen_action.stop()

        except Exception as e:
            logger.error(f"[{call.id}] Failed to play TTS response: {e}", exc_info=True)
            await call.play_tts(text="I am sorry, a system error occurred.")

if __name__ == "__main__":
    # Ensure all critical services and credentials are provided
    if not all([SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, TTS_ORCHESTRATOR_URL, REDIS_URL]):
        logger.critical("FATAL: Missing critical environment variables for relay server. Check SIGNALWIRE credentials, TTS_ORCHESTRATOR_URL, and REDIS_URL.")
    else:
        # Main execution loop to ensure the agent reconnects if the connection drops.
        while True:
            try:
                agent = VoiceAIAgent()
                agent.run()
            except Exception as e:
                logger.error(f"Agent crashed with error: {e}. Restarting in 5 seconds.")
                time.sleep(5)
