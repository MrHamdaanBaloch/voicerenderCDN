import logging
import os
import asyncio
import json
import random
import uuid
import base64
from fastapi import FastAPI, WebSocket, Response, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Connect, Stream, Play, Start
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
import redis
import aiofiles

# --- Load Environment Variables & Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VoiceAgentService")

# --- FastAPI App Setup ---
app = FastAPI()

# --- Global Configuration & Clients ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_SPACE_URL = os.environ.get("SIGNALWIRE_SPACE_URL")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

TELEPHONY_CODEC = "pcm_mulaw"
OPTIMIZED_AUDIO_DIR = "public_audio"
RAW_AUDIO_DIR = "temp_raw_audio"

groq_client = Groq(api_key=GROQ_API_KEY)
# Correctly configure keepalive at the client level as per official documentation (string or bool per SDK)
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, config)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup & TTS Logic ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

async def generate_tts_mulaw_bytes_for_stream(text: str, call_sid: str) -> bytes:
    """Generates raw pcm_mulaw audio bytes suitable for a media stream."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{call_sid}] TTS Request [{request_id}]: Generating mu-law bytes for stream. Text: '{text[:50]}...'")
    raw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_raw.wav")
    mulaw_filepath = os.path.join(RAW_AUDIO_DIR, f"{request_id}_mulaw.raw")

    try:
        # Synchronous API call to Groq (blocking) — we call this from a background task to avoid blocking main loop
        tts_response = groq_client.audio.speech.create(model="playai-tts", voice="Arista-PlayAI", input=text)
        tts_response.write_to_file(raw_filepath)

        command = [
            "ffmpeg", "-y", "-i", raw_filepath,
            "-ar", "8000", "-ac", "1",
            "-f", "mulaw", mulaw_filepath
        ]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f"ffmpeg mu-law conversion failed: {stderr.decode()}")

        async with aiofiles.open(mulaw_filepath, 'rb') as f:
            audio_bytes = await f.read()
        
        logger.info(f"[{call_sid}] TTS Request [{request_id}]: Successfully generated {len(audio_bytes)} bytes of mu-law audio.")
        return audio_bytes
    finally:
        cleanup_file(raw_filepath)
        cleanup_file(mulaw_filepath)

def cleanup_file(path: str):
    """Safely removes a file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {path}: {e}")

async def delayed_cleanup(path: str, delay: int):
    """Waits for a delay then cleans up a file."""
    await asyncio.sleep(delay)
    cleanup_file(path)

# --- Chunked outbound sender (replaces single large send) ---
async def send_audio_payload_chunked(websocket: WebSocket, stream_sid: str, audio_bytes: bytes, frame_ms: int = 20, sample_rate: int = 8000, call_sid: str = None):
    """
    Send mu-law outbound audio to SignalWire as many small frames to mimic real-time.
    For 8kHz, bytes_per_ms = 8 -> 20ms frame = 160 bytes.
    """
    bytes_per_ms = sample_rate // 1000
    frame_size = bytes_per_ms * frame_ms  # e.g., 160 bytes for 20ms @8000Hz
    total = len(audio_bytes)
    pos = 0

    logger.info(f"[{call_sid}] Streaming {total} bytes to SignalWire in {frame_size}-byte frames (~{frame_ms}ms each)")

    # Send in chunks; pace at approximately frame_ms milliseconds between frames
    try:
        while pos < total:
            chunk = audio_bytes[pos:pos + frame_size]
            payload = base64.b64encode(chunk).decode("utf-8")
            media_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"track": "outbound", "payload": payload}
            }
            await websocket.send_text(json.dumps(media_message))
            pos += frame_size
            # sleep a small amount to simulate real-time playback
            await asyncio.sleep(frame_ms / 1000.0)
    except Exception as e:
        logger.exception(f"[{call_sid}] Error while streaming outbound audio chunks: {e}")

# --- FastAPI Endpoints (Decoupled Welcome Message Architecture) ---

@app.get("/")
async def root():
    return {"message": "Voice Agent Service is running and ready to receive calls."}

@app.post("/incoming_call")
async def handle_incoming_call(request: Request):
    """Responds with cXML to connect the call to our WebSocket for bidirectional streaming."""
    body = await request.form()
    call_sid = body.get("CallSid")
    logger.info(f"📞 INCOMING CALL [{call_sid}]: From: {body.get('From', 'N/A')}, To: {body.get('To', 'N/A')}")
    
    if not RENDER_EXTERNAL_URL:
        logger.critical("CRITICAL ERROR: RENDER_EXTERNAL_URL environment variable not set. Cannot process calls.")
        raise HTTPException(status_code=503, detail="Service Unavailable: Critical configuration is missing.")

    response = VoiceResponse()
    
    # Use the stable, non-blocking handoff architecture to survive Render's cold starts.
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    
    start = Start()
    start.stream(url=websocket_url, track='both_tracks')
    response.append(start)

    # Play a welcome message using native TTS to keep the call active.
    response.say(
        "Welcome, please wait a moment while I connect you.",
        voice="en-US-Standard-A"
    )

    # Pause to keep the line open, giving the WebSocket time to establish.
    response.pause(length=60)
    
    logger.info(f"[{call_sid}] Responding with resilient cXML (<Start><Stream>, <Say>, <Pause>) to URL: {websocket_url}")
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional audio stream between SignalWire and Deepgram."""
    await websocket.accept()
    logger.info(f"🎙️ WebSocket connection established for call {call_sid}")

    # Create Deepgram live connection instance
    dg_connection = deepgram_client.listen.asynclive.v("1")

    # Buffer and readiness coordination
    incoming_buffer = []
    dg_ready = asyncio.Event()
    stop_keepalive = asyncio.Event()
    stream_sid = None

    # --- process_and_respond: takes transcript and triggers LLM + TTS (non-blocking) ---
    async def process_and_respond(transcript: str, stream_sid_local: str):
        logger.info(f"[{call_sid}] PROCESSING transcript: '{transcript}'")
        redis_key = f"conversation:{call_sid}"
        
        try:
            history_json = redis_client.get(redis_key)
            conversation_history = json.loads(history_json) if history_json else []
            
            system_prompt = (
                "You are a highly responsive, friendly, and human-like voice assistant. "
                "Keep your responses concise and conversational, suitable for a real-time phone call. "
                "Your goal is to provide accurate information quickly and naturally."
            )
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": transcript})
            
            logger.info(f"[{call_sid}] Sending transcript to LLM...")
            # run blocking SDK call in thread to avoid blocking event loop
            chat_completion = await asyncio.to_thread(groq_client.chat.completions.create, messages=messages, model="llama3-8b-8192")
            llm_response_text = chat_completion.choices[0].message.content
            logger.info(f"[{call_sid}] LLM generated response: '{llm_response_text[:50]}...'")

            conversation_history.append({"role": "user", "content": transcript})
            conversation_history.append({"role": "assistant", "content": llm_response_text})
            redis_client.set(redis_key, json.dumps(conversation_history), ex=3600)

            if llm_response_text:
                # produce TTS and stream it as a background task so we don't block inbound audio handling
                async def produce_and_stream_tts(text_to_speak: str):
                    try:
                        audio_bytes = await generate_tts_mulaw_bytes_for_stream(text_to_speak, call_sid)
                        await send_audio_payload_chunked(websocket, stream_sid_local, audio_bytes, call_sid=call_sid)
                    except Exception as e:
                        logger.exception(f"[{call_sid}] Error in produce_and_stream_tts: {e}")

                asyncio.create_task(produce_and_stream_tts(llm_response_text))

        except Exception as e:
            logger.error(f"[{call_sid}] An error occurred in process_and_respond.", exc_info=True)
        
        logger.info(f"[{call_sid}] FINISHED processing transcript: '{transcript}'")

    # --- Deepgram event handlers (correct signature) ---
    async def on_message(result, **kwargs):
        try:
            # Defensive extraction for SDK shapes
            transcript = None
            try:
                transcript = result.channel.alternatives[0].transcript.strip()
            except Exception:
                # If channel isn't present or different structure, try other keys
                transcript = getattr(result, "transcript", None)
                if isinstance(transcript, str):
                    transcript = transcript.strip()
            if not transcript:
                return
        except Exception:
            logger.exception(f"[{call_sid}] Error parsing Deepgram result.")
            return

        # determine finality robustly across sdk versions
        speech_final = getattr(result, "speech_final", None)
        if speech_final is None:
            speech_final = getattr(result, "is_final", False) or (getattr(result, "type", "") == "Final")

        if transcript and speech_final:
            logger.info(f"[{call_sid}] Deepgram speech_final received: '{transcript}'")
            # spawn processing of transcript (non-blocking)
            asyncio.create_task(process_and_respond(transcript, stream_sid))

    async def on_error(error, **kwargs):
        logger.error(f"[{call_sid}] Deepgram connection error: {error}", exc_info=True)

    # register handlers
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    # --- Start Deepgram in background and setup keepalive ---
    async def start_deepgram_and_flush():
        try:
            await dg_connection.start(
                model="nova-2-phonecall",
                language="en-US",
                encoding="mulaw",
                sample_rate=8000,
                punctuate=True,
                smart_format=True,
                interim_results=False,
                vad_events=True,
                endpointing=600
            )
            logger.info(f"[{call_sid}] Successfully connected to Deepgram.")
            dg_ready.set()
            # flush buffered audio
            if incoming_buffer:
                logger.info(f"[{call_sid}] Flushing {len(incoming_buffer)} buffered frames to Deepgram.")
            while incoming_buffer:
                chunk = incoming_buffer.pop(0)
                await dg_connection.send(chunk)

        except Exception as e:
            logger.exception(f"[{call_sid}] Failed to start Deepgram: {e}")

    # Keep Deepgram alive during silences by sending short silence periodically
    async def deepgram_keepalive_task():
        SILENCE_FRAME = bytes([0xFF] * 160)  # 20ms mu-law silence @ 8kHz
        try:
            while not stop_keepalive.is_set():
                if dg_ready.is_set():
                    try:
                        await dg_connection.send(SILENCE_FRAME)
                    except Exception as e:
                        logger.debug(f"[{call_sid}] keepalive send error: {e}")
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception(f"[{call_sid}] keepalive task exception")

    # launch background tasks
    dg_start_task = asyncio.create_task(start_deepgram_and_flush())
    keepalive_task = asyncio.create_task(deepgram_keepalive_task())

    try:
        # Main loop: receive SignalWire events
        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            event = message.get('event')
            
            if event == 'connected':
                logger.info(f"[{call_sid}] SignalWire WebSocket connected. Protocol: {message.get('protocol', 'N/A')}")
            elif event == 'start':
                stream_sid = message['start'].get('streamSid') if message.get('start') else None
                logger.info(f"[{call_sid}] SignalWire stream started. SID: {stream_sid}")
                # The welcome message is now handled by the initial cXML <Say> verb.
                # No action is needed here; we just wait for user audio.
            elif event == 'media':
                # Incoming caller/callee audio frames
                media = message.get('media', {})
                payload_b64 = media.get('payload')
                if not payload_b64:
                    continue
                try:
                    payload = base64.b64decode(payload_b64)
                except Exception:
                    logger.exception(f"[{call_sid}] Failed to base64-decode media payload.")
                    continue

                # Buffer until Deepgram ready
                if not dg_ready.is_set():
                    incoming_buffer.append(payload)
                    # throttle buffer growth to avoid OOM: drop oldest if overly large
                    if len(incoming_buffer) > 1000:
                        discarded = incoming_buffer.pop(0)
                        logger.warning(f"[{call_sid}] Incoming buffer exceeded limit; discarding oldest frame.")
                else:
                    try:
                        await dg_connection.send(payload)
                    except Exception as e:
                        logger.exception(f"[{call_sid}] Error sending payload to Deepgram: {e}")
            elif event == 'stop':
                logger.info(f"[{call_sid}] SignalWire stream stopped. Closing connections.")
                break
            else:
                logger.warning(f"[{call_sid}] Received unknown event from SignalWire: {json.dumps(message)}")
    
    except Exception as e:
        logger.exception(f"[{call_sid}] CRITICAL ERROR in WebSocket handler main loop: {e}")
    finally:
        logger.info(f"[{call_sid}] Cleaning up: stopping keepalive and finishing Deepgram connection.")
        stop_keepalive.set()
        try:
            # wait a short moment for background tasks to wind down
            await asyncio.sleep(0.1)
            # finish deepgram connection gracefully (ignore errors)
            await dg_connection.finish()
        except Exception:
            logger.exception(f"[{call_sid}] Error while finishing Deepgram connection.")
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
