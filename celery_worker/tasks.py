import os
import logging
import time
from celery import shared_task
from dotenv import load_dotenv
import io
import requests
from groq import Groq
from vosk import Model, KaldiRecognizer
import json
import wave

# --- Configuration ---
load_dotenv()
logger = logging.getLogger("AuraVoice")

# --- Groq Client Initialization (for LLM only) ---
try:
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set. LLM functionality will fail.")
        groq_client = None
    else:
        groq_client = Groq(api_key=groq_api_key)
        logger.info("Celery Task: Groq client initialized.")
except Exception as e:
    logger.error(f"Failed to initialize Groq client in Celery worker: {e}", exc_info=True)
    groq_client = None

# --- Vosk Model Initialization ---
VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "vosk-model-small-en-us-0.15")
try:
    if not os.path.exists(VOSK_MODEL_PATH):
        logger.error(f"Vosk model not found at '{VOSK_MODEL_PATH}'. Please download and place it correctly. STT will fail.")
        vosk_model = None
    else:
        vosk_model = Model(VOSK_MODEL_PATH)
        logger.info(f"Vosk STT model loaded successfully from '{VOSK_MODEL_PATH}'.")
except Exception as e:
    logger.error(f"Failed to initialize Vosk model from '{VOSK_MODEL_PATH}': {e}", exc_info=True)
    vosk_model = None

@shared_task(name="get_llm_response_task", bind=True, max_retries=3, default_retry_delay=5)
def get_llm_response_task(self, call_id: str, recording_url: str, conversation_history: list) -> dict | None:
    """
    This task takes a user's voice recording, transcribes it using a local Vosk model,
    gets a response from an LLM, and returns both the LLM response and the user's transcript.
    """
    if not groq_client or not vosk_model:
        logger.error(f"[{call_id}] A critical service (Groq or Vosk) is not available. Retrying task...")
        raise self.retry()

    logger.info(f"[{call_id}] Celery task started for STT/LLM processing.")

    try:
        # --- Step 1: Download audio ---
        logger.info(f"[{call_id}] Attempting to download audio from SignalWire...")
        download_start_time = time.monotonic()
        auth = (os.environ["SIGNALWIRE_PROJECT_ID"], os.environ["SIGNALWIRE_API_TOKEN"])
        response = requests.get(recording_url, auth=auth, timeout=10)
        response.raise_for_status()
        audio_bytes = response.content
        download_end_time = time.monotonic()
        download_latency = (download_end_time - download_start_time) * 1000
        logger.info(f"[{call_id}] Audio downloaded in {download_latency:.2f} ms.")

        # --- Step 2: STT with Vosk (includes implicit VAD) ---
        logger.info(f"[{call_id}] Transcribing audio with Vosk...")
        stt_start_time = time.monotonic()
        
        # Use wave module to handle WAV headers and stream audio data
        with io.BytesIO(audio_bytes) as wav_io:
            with wave.open(wav_io, 'rb') as wf:
                # Verify audio format
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    logger.error(f"[{call_id}] Audio file has an unsupported format.")
                    return None
                
                # The sample rate is set to 8000 Hz for telephony
                rec = KaldiRecognizer(vosk_model, wf.getframerate())
                rec.SetWords(True)
                
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        transcript_text = result.get('text', '')
        
        stt_end_time = time.monotonic()
        stt_latency = (stt_end_time - stt_start_time) * 1000
        logger.info(f"[{call_id}] Vosk STT Latency: {stt_latency:.2f} ms")
        
        logger.info(f"[{call_id}] Transcript: '{transcript_text}'")
        if not transcript_text.strip():
            logger.info(f"[{call_id}] Vosk returned empty transcript. Discarding.")
            return None

        # --- Step 3: LLM ---
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
        logger.error(f"[{call_id}] Unhandled exception in Celery STT/LLM task: {e}", exc_info=True)
        return None
