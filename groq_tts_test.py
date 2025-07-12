import logging
import asyncio
import os
import sys
from urllib.parse import quote
from dotenv import load_dotenv
from signalwire.relay.consumer import Consumer
from signalwire.relay.calling import Call
import aiohttp

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_CONTEXT = os.environ.get("SIGNALWIRE_CONTEXT", "voiceai")
PUBLIC_URL_BASE = os.environ.get("PUBLIC_URL_BASE") 

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QualityOptimizedConsumer(Consumer):
    def setup(self):
        self.project = SIGNALWIRE_PROJECT_ID
        self.token = SIGNALWIRE_API_TOKEN
        self.contexts = [SIGNALWIRE_CONTEXT]
        logger.info(f"Quality-Optimized Consumer setup for context: '{SIGNALWIRE_CONTEXT}'")

    async def ready(self):
        logger.info("Quality-Optimized Consumer is ready!")

    async def on_incoming_call(self, call: Call):
        logger.info(f"--> EVENT: Incoming call received: {call.id} from {call.from_number}")
        await call.answer()
        logger.info(f"Call {call.id} answered successfully.")

        text_to_speak = "Hello! This is a high-quality, pre-transcoded audio stream from Groq, optimized for the best possible experience on this call."
        
        try:
            encoded_text = quote(text_to_speak)
            generation_url = f"{PUBLIC_URL_BASE}/generate-optimized-tts?text={encoded_text}"
            logger.info(f"STEP 1: Requesting optimized audio from server: {generation_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(generation_url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Audio server returned an error: {response.status} - {error_text}")
                        raise Exception("Audio generation server failed.")
                    
                    response_json = await response.json()
                    optimized_filename = response_json.get("filename")

            if not optimized_filename:
                raise Exception("Audio server did not return a valid filename.")

            logger.info(f"STEP 2: Audio server successfully generated and optimized file: {optimized_filename}")

            final_audio_url = f"{PUBLIC_URL_BASE}/audio/{optimized_filename}"
            logger.info(f"STEP 3: Requesting SignalWire to play optimized audio from: {final_audio_url}")
            
            play_result = await call.play_audio(url=final_audio_url)
            
            if play_result.successful:
                logger.info("STEP 4: SignalWire confirmed playback of optimized audio completed successfully.")
            else:
                logger.error(f"STEP 4: SignalWire reported playback failed. Event: {play_result.event}")

        except Exception as e:
            logger.error(f"An error occurred during the process: {e}", exc_info=True)
            await call.play_tts(text="I am sorry, a system error occurred.")
        finally:
            logger.info(f"STEP 5: Hanging up call {call.id}.")
            await call.hangup()
            logger.info(f"--> EVENT: Call {call.id} finished.")

def main():
    if not all([SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, PUBLIC_URL_BASE]):
        logger.critical("Missing critical environment variables.")
        return
        
    consumer = QualityOptimizedConsumer()
    try:
        logger.info("Starting Quality-Optimized Consumer...")
        consumer.run()
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user.")
    finally:
        logger.info("Consumer process finished.")

if __name__ == "__main__":
    main()
