import os
import logging
import time
from celery import shared_task
from dotenv import load_dotenv
import io
import requests
from groq import Groq

# --- Configuration ---
load_dotenv()
logger = logging.getLogger("AuraVoice")

# --- Groq Client Initialization ---
try:
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set. Celery worker cannot function.")
        groq_client = None
    else:
        groq_client = Groq(api_key=groq_api_key)
        logger.info("Celery Task: Groq client initialized.")
except Exception as e:
    logger.error(f"Failed to initialize Groq client in Celery worker: {e}", exc_info=True)
    groq_client = None

@shared_task(name="get_llm_response_task", bind=True, max_retries=3, default_retry_delay=5)
def get_llm_response_task(self, call_id: str, recording_url: str) -> str | None:
    """
    This task takes a user's voice recording, transcribes it, gets a response
    from an LLM, and returns the text response. It does NOT handle TTS.
    """
    if not groq_client:
        logger.error(f"[{call_id}] Groq client not available. Retrying task...")
        raise self.retry()

    logger.info(f"[{call_id}] Celery task started for STT/LLM processing.")

    try:
        # --- Step 1: Download audio ---
        auth = (os.environ["SIGNALWIRE_PROJECT_ID"], os.environ["SIGNALWIRE_API_TOKEN"])
        response = requests.get(recording_url, auth=auth, timeout=15)
        response.raise_for_status()
        audio_buffer = io.BytesIO(response.content)
        audio_buffer.name = "recording.wav"
        
        # --- Step 2: STT ---
        logger.info(f"[{call_id}] Transcribing audio...")
        stt_start_time = time.monotonic()
        transcription = groq_client.audio.transcriptions.create(
            file=(audio_buffer.name, audio_buffer.read()),
            model="whisper-large-v3"
        )
        stt_end_time = time.monotonic()
        stt_latency = (stt_end_time - stt_start_time) * 1000
        logger.info(f"[{call_id}] Groq STT Latency: {stt_latency:.2f} ms")
        
        transcript_text = transcription.text
        logger.info(f"[{call_id}] Transcript: '{transcript_text}'")
        if not transcript_text.strip():
            return None # Return None if user said nothing

        # --- Step 3: LLM ---
        logger.info(f"[{call_id}] Generating chat completion...")
        llm_start_time = time.monotonic()
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a friendly and helpful voice assistant. Keep your responses concise and conversational."},
                {"role": "user", "content": transcript_text},
            ],
            model="llama3-8b-8192",
        )
        llm_end_time = time.monotonic()
        llm_latency = (llm_end_time - llm_start_time) * 1000
        logger.info(f"[{call_id}] Groq LLM Latency: {llm_latency:.2f} ms")

        llm_response_text = chat_completion.choices[0].message.content
        logger.info(f"[{call_id}] LLM Response: '{llm_response_text}'")
        
        return llm_response_text

    except Exception as e:
        logger.error(f"[{call.id}] Unhandled exception in Celery STT/LLM task: {e}", exc_info=True)
        # Returning None will signal the relay server that something went wrong.
        return None
