import os
import json
import base64
import logging
import asyncio
import wave
import audioop
import queue # Import the standard queue module
import time # Added for latency measurement
import aiofiles # Added for async file operations
import uuid # Added for unique IDs for temporary files
from typing import Optional, List

from fastapi import FastAPI, WebSocket, Request, Response, HTTPException
from starlette.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from groq import Groq
import redis

# -------------------------------
# Setup & Config
# -------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("VoiceAgentService")

app = FastAPI()

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
SIGNALWIRE_API_TOKEN = os.getenv("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_CONTEXT = os.getenv("SIGNALWIRE_CONTEXT")
SIGNALWIRE_PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_SPACE_URL = os.getenv("SIGNALWIRE_SPACE_URL")

# Proactive Silence Prompting Configuration
SILENCE_TIMEOUT_SECONDS = int(os.getenv("SILENCE_TIMEOUT_SECONDS", "7")) # Default to 7 seconds
SILENCE_PROMPT_TEXT = os.getenv("SILENCE_PROMPT_TEXT", "Are you still there? How can I help?")

# Groq TTS Configuration
GROQ_TTS_MODEL = os.getenv("GROQ_TTS_MODEL", "playai-tts")
GROQ_TTS_VOICE = os.getenv("GROQ_TTS_VOICE", "Fritz-PlayAI")

# LLM Configuration
LLM_SYSTEM_PROMPT = os.getenv("LLM_SYSTEM_PROMPT", "You are a helpful, professional, and concise AI assistant. Respond naturally, like a human, keeping your responses under 20 words. Maintain a positive and engaging tone, and always strive to provide value to the user.")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3-8b-8192")

# Deepgram Barge-in Configuration
DEEPGRAM_BARGE_IN_CONFIDENCE_THRESHOLD = float(os.getenv("DEEPGRAM_BARGE_IN_CONFIDENCE_THRESHOLD", "0.6"))

if not DEEPGRAM_API_KEY:
    raise RuntimeError("DEEPGRAM_API_KEY is not set in .env file")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in .env file")
if not SIGNALWIRE_API_TOKEN:
    raise RuntimeError("SIGNALWIRE_API_TOKEN is not set in .env file")
if not SIGNALWIRE_PROJECT_ID:
    raise RuntimeError("SIGNALWIRE_PROJECT_ID is not set in .env file")
if not RENDER_EXTERNAL_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is not set in .env file. Required for SignalWire callbacks.")
# SIGNALWIRE_SPACE_URL and SIGNALWIRE_CONTEXT are often used but not strictly required for basic streaming
if not SIGNALWIRE_SPACE_URL:
    logger.warning("SIGNALWIRE_SPACE_URL is not set in .env file. This might be needed for some SignalWire operations.")
if not SIGNALWIRE_CONTEXT:
    logger.warning("SIGNALWIRE_CONTEXT is not set in .env file. This might be needed for some SignalWire operations.")

# Initialize clients
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

redis_client: Optional[redis.Redis] = (
    redis.from_url(REDIS_URL) if REDIS_URL else None
)

# Public dir to save converted WAVs for quick download
PUBLIC_AUDIO_DIR = "public_audio"
RAW_AUDIO_DIR = "temp_raw_audio" # Directory for temporary raw audio files
os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)
os.makedirs(RAW_AUDIO_DIR, exist_ok=True) # Ensure temp raw audio dir exists
app.mount("/audio", StaticFiles(directory=PUBLIC_AUDIO_DIR), name="audio")

# Queue to hold transcripts for Groq processing (thread-safe for Deepgram thread)
transcript_queue = queue.Queue()

# Dictionary to hold ongoing transcripts for each call_sid
call_transcript_buffers = {}

# Dictionary to hold WebSocket and stream_sid for each active call
call_state = {}

# -------------------------------
# TTS Logic & Helpers
# -------------------------------
def cleanup_file(path: str):
    """Safely removes a file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {path}: {e}")

async def generate_tts_mulaw_bytes_for_stream(text: str, call_sid: str) -> bytes:
    """Generates raw pcm_mulaw audio bytes suitable for a media stream."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{call_sid}] TTS Request [{request_id}]: Generating mu-law bytes for stream. Text: '{text[:50]}...'")
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    mulaw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_mulaw.raw")

    try:
        tts_response = groq_client.audio.speech.create(model=GROQ_TTS_MODEL, voice=GROQ_TTS_VOICE, input=text)
        tts_response.write_to_file(raw_filepath)

        raw_file_size = os.path.getsize(raw_filepath) if os.path.exists(raw_filepath) else 0
        logger.info(f"[{call_sid}] TTS Request [{request_id}]: Raw WAV file generated by Groq TTS size: {raw_file_size} bytes.")

        if not os.path.exists(raw_filepath) or raw_file_size == 0:
            logger.error(f"[{call_sid}] TTS Request [{request_id}]: Groq TTS produced empty or missing raw WAV file: {raw_filepath}")
            raise Exception("Groq TTS produced empty or missing raw WAV file.")

        command = [
            "ffmpeg", "-y", "-i", raw_filepath,
            "-ar", "8000", "-ac", "1",
            "-f", "mulaw", mulaw_filepath
        ]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()
        if process.returncode != 0:
            logger.error(f"[{call_sid}] TTS Request [{request_id}]: ffmpeg mu-law conversion failed. Stderr: {stderr.decode()}")
            raise Exception(f"ffmpeg mu-law conversion failed: {stderr.decode()}")

        async with aiofiles.open(mulaw_filepath, 'rb') as f:
            audio_bytes = await f.read()
        
        if not audio_bytes:
            logger.error(f"[{call_sid}] TTS Request [{request_id}]: FFMPEG produced empty mu-law audio file.")
            raise Exception("FFMPEG produced empty mu-law audio file.")

        logger.info(f"[{call_sid}] TTS Request [{request_id}]: Successfully generated {len(audio_bytes)} bytes of mu-law audio.")

        # Save the generated mu-law audio to a WAV file for verification
        try:
            pcm_bytes = audioop.ulaw2lin(audio_bytes, 2) # Convert mu-law to 16-bit PCM
            output_wav_path = os.path.join(PUBLIC_AUDIO_DIR, f"groq-tts-{request_id}.wav")
            with wave.open(output_wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 2 bytes for 16-bit PCM
                wf.setframerate(8000)
                wf.writeframes(pcm_bytes)
            logger.info(f"[{call_sid}] TTS Request [{request_id}]: Saved generated TTS to {output_wav_path} for verification.")
        except Exception as e:
            logger.error(f"[{call_sid}] TTS Request [{request_id}]: Failed to save verification WAV file: {e}")

        return audio_bytes
    finally:
        cleanup_file(raw_filepath)
        cleanup_file(mulaw_filepath)

async def send_audio_payload_chunked(websocket: WebSocket, stream_sid: str, audio_bytes: bytes, frame_ms: int = 20, sample_rate: int = 8000, call_sid: str = None, user_is_speaking_event: asyncio.Event = None, agent_is_speaking_event: asyncio.Event = None):
    """
    Send mu-law outbound audio to SignalWire as many small frames to mimic real-time.
    """
    bytes_per_ms = sample_rate // 1000
    frame_size = bytes_per_ms * frame_ms
    total = len(audio_bytes)
    pos = 0
    logger.info(f"[{call_sid}] [OUTBOUND_AUDIO] Starting to stream {total} bytes to SignalWire in {frame_size}-byte frames.")
    chunk_count = 0
    try:
        # agent_is_speaking_event.set() is now handled in process_transcripts_with_groq
        if call_sid in call_state:
            call_state[call_sid]["last_activity_time"] = time.time() # Reset activity time when agent starts speaking
        while pos < total:
            if user_is_speaking_event and user_is_speaking_event.is_set():
                logger.info(f"[{call_sid}] [BARGE-IN] User started speaking. Interrupting TTS playback.")
                break
            chunk_count += 1
            chunk = audio_bytes[pos:pos + frame_size]
            if not chunk:
                logger.warning(f"[{call_sid}] [OUTBOUND_AUDIO] Empty chunk generated at pos {pos}. Skipping.")
                pos += frame_size # Advance to prevent infinite loop
                continue
            payload = base64.b64encode(chunk).decode("utf-8")
            logger.debug(f"[{call_sid}] [OUTBOUND_AUDIO] Sending chunk {chunk_count}, size {len(chunk)} bytes, payload length {len(payload)}")
            media_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"track": "outbound", "payload": payload}
            }
            try:
                await websocket.send_text(json.dumps(media_message))
            except Exception as ws_e:
                logger.error(f"[{call_sid}] [OUTBOUND_AUDIO] Failed to send WebSocket message for chunk {chunk_count}: {ws_e}")
                raise # Re-raise to be caught by the main media_ws handler
            pos += frame_size
            await asyncio.sleep(frame_ms / 1000.0)
        logger.info(f"[{call_sid}] [OUTBOUND_AUDIO] Finished streaming {chunk_count} chunks.")
        if agent_is_speaking_event:
            agent_is_speaking_event.clear() # Agent finished speaking
            if call_sid in call_state:
                call_state[call_sid]["last_activity_time"] = time.time() # Reset activity time when agent finishes speaking
    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] [OUTBOUND_AUDIO] Client disconnected during audio streaming. Halting.")
        raise # Re-raise to be caught by the main media_ws handler
    except Exception as e:
        logger.exception(f"[{call_sid}] [OUTBOUND_AUDIO] Unexpected error while streaming outbound audio chunks: {e}")
        raise # Re-raise to be caught by the main media_ws handler

# -------------------------------
# Redis helpers (optional)
# -------------------------------
def _r_append(key: str, data: bytes) -> None:
    if not redis_client:
        return
    try:
        redis_client.append(key, data)
    except Exception as e:
        logger.exception(f"Redis append failed for {key}: {e}")

def _r_expire(key: str, seconds: int) -> None:
    if not redis_client:
        return
    try:
        redis_client.expire(key, seconds)
    except Exception as e:
        logger.exception(f"Redis expire failed for {key}: {e}")

def _r_get(key: str) -> Optional[bytes]:
    if not redis_client:
        return None
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.exception(f"Redis get failed for {key}: {e}")
        return None

# -------------------------------
# Deepgram Event Handlers
# -------------------------------
def on_deepgram_open(self, *args, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    logger.info(f"[{call_sid}] Deepgram OPEN")
    # Store start time for latency measurement
    kwargs['deepgram_start_time'] = time.time()

def on_deepgram_transcript(self, result, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    user_is_speaking_event = kwargs.get('user_is_speaking_event')
    agent_is_speaking_event = kwargs.get('agent_is_speaking_event') # Retrieve agent_is_speaking_event
    
    # --- ECHO SUPPRESSION: Ignore transcripts if agent is speaking ---
    if agent_is_speaking_event and agent_is_speaking_event.is_set():
        logger.debug(f"[{call_sid}] [ECHO_SUPPRESSION] Ignoring Deepgram transcript while agent is speaking.")
        return
    # --- END ECHO SUPPRESSION ---

    try:
        if result.is_final:
            transcript = result.channel.alternatives[0].transcript
            if transcript:
                # Accumulate final transcripts into the buffer
                call_transcript_buffers.setdefault(call_sid, []).append(transcript)
                logger.info(f"[{call_sid}] 📝 Deepgram Final Transcript (accumulating): {transcript}")
                if user_is_speaking_event and transcript.strip():
                    user_is_speaking_event.set() # User is speaking, set event for barge-in
        else:
            # --- LOW-LATENCY, CONFIDENCE-BASED BARGE-IN ---
            interim_transcript = result.channel.alternatives[0].transcript
            confidence = result.channel.alternatives[0].confidence
            if interim_transcript and confidence and confidence > DEEPGRAM_BARGE_IN_CONFIDENCE_THRESHOLD:
                logger.info(f"[{call_sid}] 📝 Deepgram Interim Transcript (Confidence {confidence:.2f} > {DEEPGRAM_BARGE_IN_CONFIDENCE_THRESHOLD}): {interim_transcript}")
                if user_is_speaking_event and not user_is_speaking_event.is_set():
                    user_is_speaking_event.set() # User is speaking, set event for barge-in
                    logger.info(f"[{call_sid}] [BARGE-IN] User started speaking based on interim transcript confidence.")
            else:
                if interim_transcript:
                    logger.debug(f"[{call_sid}] 📝 Deepgram Interim Transcript (Confidence {confidence:.2f}): {interim_transcript}")
            # --- END LOW-LATENCY, CONFIDENCE-BASED BARGE-IN ---
    except Exception as e:
        logger.error(f"[{call_sid}] Error processing Deepgram transcript: {e}")

def on_deepgram_utterance_end(self, utterance_end, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    user_is_speaking_event = kwargs.get('user_is_speaking_event')
    agent_is_speaking_event = kwargs.get('agent_is_speaking_event') # Retrieve agent_is_speaking_event
    
    was_interruption = False
    if agent_is_speaking_event and agent_is_speaking_event.is_set():
        was_interruption = True # User spoke while agent was speaking

    if call_sid in call_transcript_buffers and call_transcript_buffers[call_sid]:
        full_utterance = " ".join(call_transcript_buffers[call_sid])
        logger.info(f"[{call_sid}] 🗣️ Utterance End Detected. Full utterance: '{full_utterance}'")
        
        # Measure latency from Deepgram start to utterance end
        deepgram_start_time = kwargs.get('deepgram_start_time')
        if deepgram_start_time:
            latency = (time.time() - deepgram_start_time) * 1000
            logger.info(f"[{call_sid}] ⏱️ Deepgram Utterance End Latency: {latency:.2f} ms")
        
        # Pass was_interruption along with other data
        transcript_queue.put((full_utterance, time.time(), call_sid, user_is_speaking_event, was_interruption)) 
        call_transcript_buffers[call_sid].clear() # Clear buffer after sending to Groq
    else:
        logger.debug(f"[{call_sid}] Utterance End detected but no accumulated transcript.")
    
    if user_is_speaking_event:
        user_is_speaking_event.clear() # User finished speaking, clear event
    
    # Update last activity time for silence detection
    if call_sid in call_state:
        call_state[call_sid]["last_activity_time"] = time.time()

def on_deepgram_speech_started(self, speech_started, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    user_is_speaking_event = kwargs.get('user_is_speaking_event')
    agent_is_speaking_event = kwargs.get('agent_is_speaking_event') # Retrieve agent_is_speaking_event

    # --- ECHO SUPPRESSION: Ignore SpeechStarted if agent is speaking ---
    if agent_is_speaking_event and agent_is_speaking_event.is_set():
        logger.debug(f"[{call_sid}] [ECHO_SUPPRESSION] Ignoring Deepgram SpeechStarted while agent is speaking.")
        return
    # --- END ECHO SUPPRESSION ---

    logger.info(f"[{call_sid}] 🗣️ Deepgram Speech Started event received.")
    # Removed direct setting of user_is_speaking_event here.
    # Barge-in will now rely solely on confidence-based interim transcripts.
    
    # Update last activity time for silence detection
    if call_sid in call_state:
        call_state[call_sid]["last_activity_time"] = time.time()

def on_deepgram_error(self, error, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    logger.error(f"[{call_sid}] Deepgram ERROR: {error}")

def on_deepgram_close(self, *args, **kwargs):
    call_sid = kwargs.get('call_sid', 'unknown')
    logger.info(f"[{call_sid}] Deepgram CLOSE")

# -------------------------------
# HTTP Routes
# -------------------------------
@app.get("/")
async def root():
    return {"message": "OK: Voice Agent Service up"}

@app.post("/incoming_call")
async def incoming_call(request: Request):
    """
    Respond with <Start><Stream> to route call audio to our WebSocket.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    frm = form.get("From", "N/A"); to = form.get("To", "N/A")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {frm}, To: {to}")

    if not RENDER_EXTERNAL_URL:
        raise HTTPException(status_code=503, detail="RENDER_EXTERNAL_URL not set")

    host = RENDER_EXTERNAL_URL.replace("https://", "").replace("http://", "")
    ws_url = f"wss://{host}/media/{call_sid}"

    logger.info(f"[{call_sid}] Using RENDER_EXTERNAL_URL: {RENDER_EXTERNAL_URL} for WebSocket URL: {ws_url}")

    vr = VoiceResponse()
    connect = vr.connect()
    # Explicitly set codec and sampleRate for outbound audio to ensure SignalWire interprets it correctly
    connect.stream(url=ws_url)
    vr.pause(length=60)  # safety net to keep the call alive

    logger.info(f"[{call_sid}] Stream recording enabled.")
    twiml_response = str(vr)
    logger.info(f"[{call_sid}] Returning TwiML: {twiml_response}") # Log the full TwiML response
    return Response(content=twiml_response, media_type="application/xml")

@app.get("/save_audio/{call_sid}")
async def save_audio(call_sid: str):
    """
    Convert raw μ-law (8kHz) bytes in Redis to a mono 16-bit PCM WAV.
    """
    key = f"audio_dump:{call_sid}"
    raw = _r_get(key)
    if not raw:
        raise HTTPException(status_code=404, detail="No audio dump found (expired or missing).")

    try:
        pcm = audioop.ulaw2lin(raw, 2)  # -> 16-bit
        out_path = os.path.join(PUBLIC_AUDIO_DIR, f"{call_sid}.wav")
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm)
        logger.info(f"[{call_sid}] Saved WAV: {out_path} ({len(raw)} μ-law bytes)")
        return {"message": f"Saved to /audio/{call_sid}.wav"}
    except Exception as e:
        logger.exception(f"[{call_sid}] WAV conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert audio")

# -------------------------------
# WebSocket Route for SignalWire <Stream>
# -------------------------------
@app.websocket("/media/{call_sid}")
async def media_ws(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    logger.info(f"🎙️ WebSocket accepted for call {call_sid}")

    stream_sid: Optional[str] = None
    dump_key = f"audio_dump:{call_sid}"
    user_is_speaking_event = asyncio.Event() # Event to signal if user is speaking (for barge-in)
    agent_is_speaking_event = asyncio.Event() # Event to signal if agent is speaking (for interruption context)

    # Store websocket and events in call_state
    call_state[call_sid] = {
        "websocket": websocket,
        "user_is_speaking_event": user_is_speaking_event,
        "agent_is_speaking_event": agent_is_speaking_event,
        "last_activity_time": time.time(), # Track last user or agent activity
        "stream_sid": None, # Will be populated once 'start' event is received
        "messages": [{"role": "system", "content": LLM_SYSTEM_PROMPT}] # Initialize conversation history with system prompt
    }

    logger.info(f"[{call_sid}] WebSocket endpoint URL: {str(websocket.url)}")

    # prepare Redis key
    if redis_client:
        try:
            redis_client.delete(dump_key)
            logger.info(f"[{call_sid}] [AUDIO_DUMP] Initialized Redis key")
        except Exception as e:
            logger.exception(f"[{call_sid}] Redis init failed: {e}")

    # Deepgram live connection
    dg_conn = deepgram_client.listen.websocket.v("1")

    # Pass call_sid, latency_tracking, and user_is_speaking_event to handlers using functools.partial
    from functools import partial
    latency_tracking = {} # Dictionary to store start times for this specific call's Deepgram connection
    dg_conn.on(LiveTranscriptionEvents.Open, partial(on_deepgram_open, call_sid=call_sid, latency_tracking=latency_tracking))
    dg_conn.on(LiveTranscriptionEvents.Transcript, partial(on_deepgram_transcript, call_sid=call_sid, latency_tracking=latency_tracking, user_is_speaking_event=user_is_speaking_event, agent_is_speaking_event=agent_is_speaking_event)) # Pass agent_is_speaking_event
    dg_conn.on(LiveTranscriptionEvents.UtteranceEnd, partial(on_deepgram_utterance_end, call_sid=call_sid, latency_tracking=latency_tracking, user_is_speaking_event=user_is_speaking_event, agent_is_speaking_event=agent_is_speaking_event))
    dg_conn.on(LiveTranscriptionEvents.Error, partial(on_deepgram_error, call_sid=call_sid, latency_tracking=latency_tracking))
    dg_conn.on(LiveTranscriptionEvents.Close, partial(on_deepgram_close, call_sid=call_sid, latency_tracking=latency_tracking))
    dg_conn.on(LiveTranscriptionEvents.SpeechStarted, partial(on_deepgram_speech_started, call_sid=call_sid, user_is_speaking_event=user_is_speaking_event, agent_is_speaking_event=agent_is_speaking_event)) # Pass agent_is_speaking_event

    try:
        # Initial Greeting
        greeting_text = "Hello! Welcome to the voice agent. How can I help you today?"
        greeting_audio_bytes = await generate_tts_mulaw_bytes_for_stream(greeting_text, call_sid)
        logger.info(f"[{call_sid}] Initial greeting audio bytes length: {len(greeting_audio_bytes)}") # Log greeting audio length

        # Wait for SignalWire 'start' event to get stream_sid before sending outbound audio
        while not stream_sid:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            event = msg.get("event")
            if event == "start":
                stream_sid = (msg.get("start") or {}).get("streamSid")
                call_state[call_sid]["stream_sid"] = stream_sid # Store stream_sid in call_state
                logger.info(f"[{call_sid}] Stream START. SID: {stream_sid}")
                break
            else:
                logger.debug(f"[{call_sid}] Received {event} while waiting for 'start' event.")

        if stream_sid:
            await send_audio_payload_chunked(websocket, stream_sid, greeting_audio_bytes, call_sid=call_sid, user_is_speaking_event=user_is_speaking_event, agent_is_speaking_event=agent_is_speaking_event)
        else:
            logger.error(f"[{call_sid}] Failed to get stream_sid, cannot play welcome message.")

        # Start Deepgram with μ-law / 8 kHz to match SignalWire media frames *AFTER* greeting
        try:
            dg_conn.start(
                LiveOptions(
                    model="nova-2-phonecall", # Changed to phonecall optimized model
                    language="en-US",
                    encoding="mulaw",    # SignalWire audio format
                    sample_rate=8000,     # SignalWire audio format
                    channels=1,
                    smart_format=True,
                    interim_results=True, # Enable interim results for better human-like interaction
                    utterance_end_ms="1000", # Detect end of utterance after 1 second of silence for quicker responses (recommended by Deepgram)
                    vad_events=True, # Enable VAD events for SpeechStarted
                    endpointing="1500", # Further optimized VAD for background noise: 1500ms
                    filler_words=True # Enable filler word detection for more natural transcription
                )
            )
            logger.info(f"[{call_sid}] Deepgram START requested AFTER greeting")
            # Reset last activity time AFTER Deepgram has started listening
            if call_sid in call_state:
                call_state[call_sid]["last_activity_time"] = time.time()
                logger.info(f"[{call_sid}] Reset last_activity_time after Deepgram START.")
        except Exception as e:
            logger.exception(f"[{call_sid}] Failed to start Deepgram after greeting: {e}")
            dg_conn = None

        # Main loop to process incoming media from SignalWire
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            event = msg.get("event")

            if event == "connected":
                logger.info(f"[{call_sid}] SignalWire connected. Protocol: {msg.get('protocol', 'N/A')}")

            elif event == "start": # This should ideally only happen once, but handle defensively
                stream_sid = (msg.get("start") or {}).get("streamSid")
                logger.info(f"[{call_sid}] Stream START. SID: {stream_sid}")

            elif event == "media":
                media = msg.get("media", {})
                if media.get("track") != "inbound":
                    continue
                payload_b64 = media.get("payload")
                if not payload_b64:
                    continue

                try:
                    audio_bytes = base64.b64decode(payload_b64)
                except Exception:
                    logger.warning(f"[{call_sid}] Bad base64 payload; skipping")
                    continue

                # Optional dump
                _r_append(dump_key, audio_bytes)

                # Forward to Deepgram
                if dg_conn:
                    try:
                        dg_conn.send(audio_bytes)
                    except Exception as e:
                        logger.exception(f"[{call_sid}] Deepgram send failed: {e}")

            elif event == "stop":
                logger.info(f"[{call_sid}] Stream STOP")
                break

            else:
                logger.debug(f"[{call_sid}] Unknown event: {event}")

    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] WebSocket client disconnected")
    except Exception as e:
        logger.exception(f"[{call_sid}] WebSocket handler error: {e}")
    finally:
        _r_expire(dump_key, 3600)  # keep audio dump for 1 hour

        if dg_conn:
            try:
                await asyncio.sleep(1.0) # Give Deepgram more time to process final transcripts
                dg_conn.finish()
                logger.info(f"[{call_sid}] Deepgram FINISH")
            except Exception as e:
                logger.exception(f"[{call_sid}] Deepgram finish error: {e}")

        try:
            await websocket.close()
        except Exception:
            pass

        logger.info(f"[{call_sid}] WebSocket closed")
        # Clean up call state
        if call_sid in call_state:
            del call_state[call_sid]
            logger.info(f"[{call_sid}] Cleaned up call state.")

# -------------------------------
# Proactive Silence Detection Task
# -------------------------------
async def silence_detection_task():
    """
    Periodically checks for silence in active calls and sends a proactive prompt.
    """
    logger.info("Silence detection task started.")
    while True:
        await asyncio.sleep(1) # Check every second
        current_time = time.time()
        
        for call_sid, state in list(call_state.items()): # Iterate over a copy to avoid modification issues
            websocket = state.get("websocket")
            stream_sid = state.get("stream_sid")
            user_is_speaking = state["user_is_speaking_event"].is_set()
            agent_is_speaking = state["agent_is_speaking_event"].is_set()
            last_activity_time = state["last_activity_time"]

            if not websocket or not stream_sid:
                continue # Skip if WebSocket or stream_sid is not yet established

            if not user_is_speaking and not agent_is_speaking:
                silence_duration = current_time - last_activity_time
                if silence_duration >= SILENCE_TIMEOUT_SECONDS:
                    logger.info(f"[{call_sid}] Detected {silence_duration:.2f}s of silence. Sending proactive prompt.")
                    try:
                        prompt_audio_bytes = await generate_tts_mulaw_bytes_for_stream(SILENCE_PROMPT_TEXT, call_sid)
                        await send_audio_payload_chunked(
                            websocket,
                            stream_sid,
                            prompt_audio_bytes,
                            call_sid=call_sid,
                            user_is_speaking_event=state["user_is_speaking_event"],
                            agent_is_speaking_event=state["agent_is_speaking_event"]
                        )
                        # Reset last activity time after sending prompt
                        state["last_activity_time"] = time.time()
                    except Exception as e:
                        logger.error(f"[{call_sid}] Failed to send proactive silence prompt: {e}")

# -------------------------------
# Groq Processing Task
# -------------------------------
async def process_transcripts_with_groq():
    """
    Continuously pulls transcripts from the thread-safe queue and sends them to Groq.
    """
    logger.info("Groq processing task started.")
    while True:
        try:
            transcript_data = transcript_queue.get_nowait()
            if transcript_data is None: # Sentinel value to stop the task
                logger.info("Groq task: Received stop signal.")
                break

            transcript, deepgram_utterance_end_time, call_sid, user_is_speaking_event, was_interruption = transcript_data
            
            # Measure latency from Deepgram utterance end to sending to Groq
            latency_to_groq_send = (time.time() - deepgram_utterance_end_time) * 1000
            logger.info(f"[{call_sid}] ⏱️ Latency (Utterance End to Groq Send): {latency_to_groq_send:.2f} ms")

            logger.info(f"[{call_sid}] Sending to Groq: '{transcript}'")
            groq_request_start_time = time.time()
            try:
                user_content = (
                    f"The user interrupted your previous response. Please acknowledge this and respond to their new input: {transcript}"
                    if was_interruption
                    else transcript
                )
                # Retrieve conversation history for this call
                current_call_state = call_state.get(call_sid)
                if not current_call_state:
                    logger.error(f"[{call_sid}] Call state not found for Groq processing. Cannot maintain conversation history.")
                    transcript_queue.task_done()
                    continue

                messages = current_call_state.get("messages", [])
                # Ensure system prompt is always the first message if not already present
                if not messages or messages[0]["role"] != "system":
                    messages.insert(0, {"role": "system", "content": LLM_SYSTEM_PROMPT})
                
                messages.append({"role": "user", "content": user_content})

                chat_completion = groq_client.chat.completions.create(
                    messages=messages, # Use the conversation history
                    model=LLM_MODEL, # Use configurable LLM model
                )
                groq_response_time = time.time()
                groq_response = chat_completion.choices[0].message.content
                
                # Append agent's response to conversation history
                messages.append({"role": "assistant", "content": groq_response})
                
                # Measure Groq API latency
                groq_api_latency = (groq_response_time - groq_request_start_time) * 1000
                logger.info(f"[{call_sid}] ⏱️ Groq API Latency: {groq_api_latency:.2f} ms")
                logger.info(f"[{call_sid}] 🤖 Groq Response: {groq_response}\n")

                # Generate TTS for Groq response and send back to SignalWire
                tts_audio_bytes = await generate_tts_mulaw_bytes_for_stream(groq_response, call_sid)
                
                # Retrieve websocket and stream_sid from call_state
                current_call_state = call_state.get(call_sid)
                if current_call_state and current_call_state.get("websocket") and current_call_state.get("stream_sid"):
                    websocket_for_call = current_call_state["websocket"]
                    stream_sid_for_call = current_call_state["stream_sid"]
                    websocket_for_call = current_call_state["websocket"]
                    stream_sid_for_call = current_call_state["stream_sid"]
                    user_is_speaking_event_for_call = current_call_state["user_is_speaking_event"]
                    agent_is_speaking_event_for_call = current_call_state["agent_is_speaking_event"]
                    
                    # Set agent_is_speaking_event BEFORE streaming starts
                    if agent_is_speaking_event_for_call:
                        agent_is_speaking_event_for_call.set()
                        if call_sid in call_state:
                            call_state[call_sid]["last_activity_time"] = time.time() # Reset activity time when agent starts speaking

                    await send_audio_payload_chunked(
                        websocket_for_call,
                        stream_sid_for_call,
                        tts_audio_bytes,
                        call_sid=call_sid,
                        user_is_speaking_event=user_is_speaking_event_for_call,
                        agent_is_speaking_event=agent_is_speaking_event_for_call
                    )
                else:
                    logger.error(f"[{call_sid}] Cannot send outbound TTS: WebSocket or stream_sid not found in call_state. Current call_state: {current_call_state}")

            except Exception as e:
                logger.error(f"[{call_sid}] Error getting Groq response or generating TTS: {e}")
            finally:
                transcript_queue.task_done() # Mark as done even if Groq fails
        except queue.Empty:
            await asyncio.sleep(0.1) # Wait a bit if queue is empty
            continue
        except Exception as e:
            logger.error(f"Error in Groq processing task: {e}")

# -------------------------------
# Main Application Entry Point
# -------------------------------
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_transcripts_with_groq())
    asyncio.create_task(silence_detection_task()) # Start the silence detection task
    logger.info("Voice Agent Service started.")

@app.on_event("shutdown")
async def shutdown_event():
    # Signal the Groq processing task to stop
    transcript_queue.put(None)
    logger.info("Voice Agent Service shutting down.")

if __name__ == "__main__":
    import uvicorn
    # Determine the port to run on. Use $PORT from environment (e.g., on Render) or default to 8000.
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting FastAPI application on port {port}. For local testing, ensure RENDER_EXTERNAL_URL is set to a public tunnel (e.g., ngrok) for SignalWire to connect. On Render, this will use the provided $PORT.")
    uvicorn.run(app, host="0.0.0.0", port=port)
