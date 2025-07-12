import logging
import os
import asyncio
import subprocess
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv
from tts.piper_tts import PiperTTS # Assuming piper is in this path

# --- Load Environment Variables & Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TTSOrchestrator")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEPHONY_CODEC = os.environ.get("TELEPHONY_CODEC", "pcm_mulaw") 
OPTIMIZED_AUDIO_DIR = "public_audio" # Render will use this directory
RAW_AUDIO_DIR = "temp_raw_audio"

# --- FastAPI App & Services ---
app = FastAPI()
groq_client = Groq(api_key=GROQ_API_KEY)
piper_tts_service = PiperTTS()

# --- Directory Setup ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created audio directory: {directory}")

# This serves the final, optimized audio files from the persistent disk on Render
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

# --- Helper Functions ---
def cleanup_file(path: str):
    """Removes a file and logs the action."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up file: {path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {path}: {e}")

async def generate_tts_audio(text: str, background_tasks: BackgroundTasks) -> str:
    """
    Orchestrates the generation of TTS audio, trying Groq first and falling back to Piper.
    Returns the filename of the final, optimized audio file.
    """
    request_id = str(uuid.uuid4())
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    optimized_filename = f"{request_id}_optimized.wav"
    optimized_filepath = os.path.join(OPTIMIZED_AUDIO_DIR, optimized_filename)
    
    # Schedule cleanup of the final optimized file after 10 minutes
    background_tasks.add_task(asyncio.sleep, 600)
    background_tasks.add_task(cleanup_file, optimized_filepath)

    generation_success = False
    # --- Try Groq First ---
    if GROQ_API_KEY:
        try:
            logger.info(f"Attempting Groq TTS for text: '{text[:30]}...'")
            tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
            tts_response.write_to_file(raw_filepath)
            logger.info("Groq TTS succeeded.")
            generation_success = True
        except Exception as e:
            logger.error(f"Groq TTS failed: {e}. Falling back to Piper.")

    # --- Fallback to Piper ---
    if not generation_success:
        try:
            logger.info("Attempting Piper TTS fallback.")
            if not piper_tts_service.model:
                await piper_tts_service.initialize() # Ensure model is loaded
            
            audio_bytes = await piper_tts_service.text_to_speech(text)
            if audio_bytes:
                with open(raw_filepath, "wb") as f:
                    f.write(audio_bytes)
                logger.info("Piper TTS succeeded.")
                generation_success = True
            else:
                raise Exception("Piper TTS returned no audio bytes.")
        except Exception as e:
            logger.error(f"Piper TTS fallback also failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="All TTS providers failed.")

    # --- Transcode the successful audio ---
    try:
        logger.info(f"Transcoding raw file to {TELEPHONY_CODEC} at 8kHz mono.")
        command = ["ffmpeg", "-i", raw_filepath, "-ar", "8000", "-ac", "1", "-acodec", TELEPHONY_CODEC, "-y", optimized_filepath]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"ffmpeg transcoding failed. STDERR: {stderr.decode()}")
            raise Exception("ffmpeg failed.")
        
        logger.info("Transcoding successful.")
        return optimized_filename
    finally:
        cleanup_file(raw_filepath)

# --- API Endpoints ---
@app.get("/generate-audio")
async def get_generated_audio_url(text: str, background_tasks: BackgroundTasks):
    """
    Main endpoint. Generates TTS, saves it, transcodes it, and returns the filename.
    The final URL is constructed by the client.
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text parameter is required.")
    
    filename = await generate_tts_audio(text, background_tasks)
    return {"success": True, "filename": filename}

@app.get("/")
def read_root():
    return {"message": "TTS Orchestrator is running."}

logger.info("TTS Orchestrator configured.")
