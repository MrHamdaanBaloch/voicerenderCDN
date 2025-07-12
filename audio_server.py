import logging
import os
import asyncio
import subprocess
import uuid
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SERVER_PORT = 8081
# You can switch this to 'pcm_alaw' in your .env file if you are outside North America/Japan
TELEPHONY_CODEC = os.environ.get("TELEPHONY_CODEC", "pcm_mulaw") 
RAW_AUDIO_DIR = "temp_raw_audio"
OPTIMIZED_AUDIO_DIR = "public_optimized_audio"

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI()
groq_client = Groq(api_key=GROQ_API_KEY)

for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created audio directory: {directory}")

app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

async def verify_audio_properties(filepath: str):
    """Uses ffprobe to verify the properties of the transcoded audio file."""
    try:
        command = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels", "-of", "json", filepath]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            audio_info = json.loads(stdout.decode()).get("streams", [{}])[0]
            logger.info(f"VERIFIED AUDIO PROPERTIES: {audio_info}")
            # You can add assertions here if needed, e.g.:
            # assert audio_info.get("codec_name") == TELEPHONY_CODEC.replace("pcm_", "")
            # assert audio_info.get("sample_rate") == "8000"
        else:
            logger.warning(f"ffprobe verification failed. STDERR: {stderr.decode()}")
    except Exception as e:
        logger.error(f"An error occurred during ffprobe verification: {e}", exc_info=True)

async def generate_and_optimize_tts(text: str) -> str:
    request_id = str(uuid.uuid4())
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    optimized_filepath = os.path.join(OPTIMIZED_AUDIO_DIR, f"{request_id}_optimized.wav")
    
    try:
        logger.info(f"Generating raw audio for: '{text}'")
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)
        logger.info(f"Raw audio saved to: {raw_filepath}")

        logger.info(f"Transcoding to {TELEPHONY_CODEC} at 8kHz mono.")
        command = ["ffmpeg", "-i", raw_filepath, "-ar", "8000", "-ac", "1", "-acodec", TELEPHONY_CODEC, "-y", optimized_filepath]
        
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"ffmpeg transcoding failed. Error: {stderr.decode()}")
            raise Exception("ffmpeg failed.")
        
        logger.info("Transcoding successful.")
        await verify_audio_properties(optimized_filepath)
        return os.path.basename(optimized_filepath)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return None
    finally:
        if os.path.exists(raw_filepath):
            os.remove(raw_filepath)

@app.get("/generate-optimized-tts")
async def get_optimized_tts(text: str):
    if not text:
        raise HTTPException(status_code=400, detail="Text parameter is required.")
    
    optimized_filename = await generate_and_optimize_tts(text)
    
    if optimized_filename:
        return {"success": True, "filename": optimized_filename}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate or optimize audio.")

@app.get("/")
def read_root():
    return {"message": "High-quality, pre-transcoded TTS audio server is running."}
