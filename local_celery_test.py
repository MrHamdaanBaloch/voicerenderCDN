import os
import uuid
import json
import time
import logging
from dotenv import load_dotenv
import redis

# Import the Celery app and the task we want to test
from celery_worker.celery_app import celery_app
from celery_worker.tasks import process_call_recording

# --- Setup ---
load_dotenv()
logger = logging.getLogger("AuraVoiceTest")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Test Configuration ---
# A public, short sample WAV file for testing.
# This simulates the URL that SignalWire would provide.
TEST_RECORDING_URL = "http://www.moviesoundclips.net/movies1/gladiator/memorable.wav"

# A fake call ID for this test run.
TEST_CALL_ID = f"local-test-{uuid.uuid4()}"

def run_local_test():
    """
    Dispatches a test task to the Celery worker to test the full pipeline locally.
    """
    logger.info("--- STARTING LOCAL CELERY PIPELINE TEST ---")

    # Verify that Redis is running
    try:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Could not connect to Redis at {redis_url}. Please ensure Redis is running.")
        logger.error(f"Error: {e}")
        return

    # Initialize a dummy conversation history for the test call
    history_key = f"history:{TEST_CALL_ID}"
    redis_client.set(history_key, json.dumps([
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]))
    logger.info(f"Initialized dummy conversation history in Redis for call ID: {TEST_CALL_ID}")

    logger.info(f"Dispatching task for call ID: {TEST_CALL_ID}")
    logger.info(f"Using recording URL: {TEST_RECORDING_URL}")

    # Dispatch the task to the Celery worker
    # .delay() is a shortcut for .apply_async()
    task_result = process_call_recording.delay(
        call_id=TEST_CALL_ID,
        recording_url=TEST_RECORDING_URL
    )

    logger.info(f"Task dispatched with ID: {task_result.id}. Waiting for completion...")
    logger.info("Check the output of your 'celery worker' terminal to see the pipeline logs in real-time.")

    try:
        # Wait for the task to finish and get the result.
        # The task itself doesn't return a value, but this will raise an exception if the task failed.
        result = task_result.get(timeout=60)
        logger.info("--- TEST SUCCEEDED ---")
        logger.info("The Celery task completed without raising an exception.")
        logger.info("Check the '/tmp/auravoice_audio_cache' directory for the generated .wav file.")
        logger.info(f"Also, check Redis for the updated history with key: '{history_key}'")

    except Exception as e:
        logger.error("--- TEST FAILED ---")
        logger.error(f"The Celery task failed with an exception: {e}", exc_info=True)

if __name__ == "__main__":
    print("-----------------------------------------------------------")
    print("AuraVoice Local Celery Test")
    print("-----------------------------------------------------------")
    print("This script will send a test job to your Celery worker.")
    print("Instructions:")
    print("1. Make sure your local Redis server is running.")
    print("2. In a separate terminal, run the Celery worker with the command:")
    print("   celery -A celery_worker.celery_app worker --loglevel=info")
    print("3. Ensure your .env file has a valid GROQ_API_KEY.")
    print("-----------------------------------------------------------")
    
    # Give the user a moment to read the instructions
    time.sleep(2)
    
    run_local_test()
