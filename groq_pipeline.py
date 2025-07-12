import os
import logging
import requests
import io
from groq import Groq
from dotenv import load_dotenv

# --- Basic Configuration ---
load_dotenv()
logger = logging.getLogger("AuraVoice") # Use the same logger as the main app

# --- Groq Client Initialization ---
try:
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        logger.warning("GROQ_API_KEY environment variable not set. The pipeline will not work.")
        groq_client = None
    else:
        groq_client = Groq(api_key=groq_api_key)
        logger.info("Groq client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}", exc_info=True)
    groq_client = None

def process_audio_with_groq(audio_url: str, sw_project_id: str, sw_token: str, output_filepath: str) -> bool:
    """
    Processes an audio URL through the full Groq pipeline (STT -> LLM -> TTS)
    and saves the final audio to a file.
    """
    if not groq_client:
        logger.error("Cannot process audio: Groq client is not available.")
        return False

    # --- Step 1: Download audio into an in-memory buffer ---
    try:
        logger.info(f"Downloading audio from: {audio_url}")
        auth = (sw_project_id, sw_token)
        response = requests.get(audio_url, auth=auth, timeout=15)
        response.raise_for_status()
        
        audio_buffer = io.BytesIO(response.content)
        audio_buffer.name = "recording.wav"
        
        logger.info("Audio downloaded successfully into memory.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download audio file from {audio_url}: {e}", exc_info=True)
        return False

    # --- Step 2: STT ---
    try:
        logger.info("Transcribing audio with Groq Whisper...")
        # We must read the buffer to pass the bytes to the file tuple
        audio_bytes = audio_buffer.read()
        transcription = groq_client.audio.transcriptions.create(
            file=(audio_buffer.name, audio_bytes),
            model="whisper-large-v3",
            response_format="json",
        )
        transcript_text = transcription.text
        logger.info(f"Transcript: '{transcript_text}'")
        if not transcript_text.strip():
            logger.warning("Transcription is empty, stopping pipeline.")
            return False

    except Exception as e:
        logger.error(f"Groq STT API call failed: {e}", exc_info=True)
        return False

    # --- Step 3: LLM ---
    try:
        logger.info("Generating chat completion with Groq LLM...")
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a friendly and helpful voice assistant. Keep your responses concise and conversational."},
                {"role": "user", "content": transcript_text},
            ],
            model="llama3-8b-8192",
        )
        llm_response_text = chat_completion.choices[0].message.content
        logger.info(f"LLM Response: '{llm_response_text}'")
    except Exception as e:
        logger.error(f"Groq Chat Completions API call failed: {e}", exc_info=True)
        return False

    # --- Step 4: Use the correct TTS method: write_to_file ---
    try:
        logger.info("Synthesizing speech with Groq TTS...")
        tts_response = groq_client.audio.speech.create(
            model="playai-tts",
            voice="Fritz-PlayAI",
            input=llm_response_text,
            speed=1.0,
            response_format="wav"
        )
        # Use the correct, documented method to save the audio.
        tts_response.write_to_file(output_filepath)
        logger.info(f"Speech synthesized successfully to {output_filepath}")
        return True
    except Exception as e:
        logger.error(f"Groq TTS API call failed: {e}", exc_info=True)
        return False
