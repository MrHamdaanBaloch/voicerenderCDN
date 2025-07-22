import os
import logging
import time
from celery import shared_task
from dotenv import load_dotenv
import io
import requests
from groq import Groq
from vad.vad_detector import VADDetector

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

# --- VAD Initialization ---
try:
    vad_detector = VADDetector()
except Exception as e:
    logger.error(f"Failed to initialize VAD detector in Celery worker: {e}", exc_info=True)
    vad_detector = None

@shared_task(name="get_llm_response_task", bind=True, max_retries=3, default_retry_delay=5)
def get_llm_response_task(self, call_id: str, recording_url: str, conversation_history: list) -> dict | None:
    """
    This task takes a user's voice recording, transcribes it, gets a response
    from an LLM with conversation history, and returns both the LLM response
    and the user's transcript.
    """
    if not groq_client or not vad_detector:
        logger.error(f"[{call_id}] A critical service (Groq or VAD) is not available. Retrying task...")
        raise self.retry()

    logger.info(f"[{call_id}] Celery task started for VAD/STT/LLM processing.")

    try:
        # --- Step 1: Download audio ---
        logger.info(f"[{call_id}] Attempting to download audio from SignalWire...")
        download_start_time = time.monotonic()
        auth = (os.environ["SIGNALWIRE_PROJECT_ID"], os.environ["SIGNALWIRE_API_TOKEN"])
        # Reduce timeout to 10s to avoid causing a full Celery task timeout.
        response = requests.get(recording_url, auth=auth, timeout=10)
        response.raise_for_status()
        audio_bytes = response.content
        download_end_time = time.monotonic()
        download_latency = (download_end_time - download_start_time) * 1000
        logger.info(f"[{call_id}] Audio downloaded in {download_latency:.2f} ms.")
        
        # --- Step 2: VAD ---
        if not vad_detector.is_speech(audio_bytes):
            logger.info(f"[{call_id}] VAD detected no speech. Discarding task.")
            return None # Return None if no speech is detected

        # --- Step 3: STT ---
        logger.info(f"[{call_id}] Transcribing audio...")
        audio_buffer = io.BytesIO(audio_bytes)
        audio_buffer.name = "recording.wav"
        stt_start_time = time.monotonic()
        transcription = groq_client.audio.transcriptions.create(
            file=(audio_buffer.name, audio_buffer.read()),
            model="distil-whisper-large-v3-en"
        )
        stt_end_time = time.monotonic()
        stt_latency = (stt_end_time - stt_start_time) * 1000
        logger.info(f"[{call_id}] Groq STT Latency: {stt_latency:.2f} ms")
        
        transcript_text = transcription.text
        logger.info(f"[{call_id}] Transcript: '{transcript_text}'")
        if not transcript_text.strip():
            return None # Return None if user said nothing

        # --- Step 4: LLM ---
        logger.info(f"[{call_id}] Generating chat completion with history...")
        llm_start_time = time.monotonic()
        
        messages = [
            {"role": "system", "content": "You are a human-like voice assistant. Your responses MUST be short, warm, and conversational. NEVER exceed 35 words. Be helpful, but get straight to the point."}
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": transcript_text})

        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
        )
        llm_end_time = time.monotonic()
        llm_latency = (llm_end_time - llm_start_time) * 1000
        logger.info(f"[{call_id}] Groq LLM Latency: {llm_latency:.2f} ms")

        llm_response_text = chat_completion.choices[0].message.content
        logger.info(f"[{call_id}] LLM Response: '{llm_response_text}'")
        
        return {
            "llm_response": llm_response_text,
            "user_transcript": transcript_text
        }

    except Exception as e:
        logger.error(f"[{call.id}] Unhandled exception in Celery STT/LLM task: {e}", exc_info=True)
        # Returning None will signal the relay server that something went wrong.
        return None
