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
# Correctly configure keepalive at the client level as per official documentation
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

async def send_audio_payload_chunked(websocket: WebSocket, stream_sid: str, audio_bytes: bytes, frame_ms: int = 20, sample_rate: int = 8000, call_sid: str = None):
    """
    Send mu-law outbound audio to SignalWire as many small frames to mimic real-time.
    """
    bytes_per_ms = sample_rate // 1000
    frame_size = bytes_per_ms * frame_ms
    total = len(audio_bytes)
    pos = 0
    logger.info(f"[{call_sid}] [BLACKBOX] Starting to stream {total} bytes to SignalWire in {frame_size}-byte frames.")
    chunk_count = 0
    try:
        while pos < total:
            chunk_count += 1
            chunk = audio_bytes[pos:pos + frame_size]
            payload = base64.b64encode(chunk).decode("utf-8")
            media_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"track": "outbound", "payload": payload}
            }
            await websocket.send_text(json.dumps(media_message))
            pos += frame_size
            await asyncio.sleep(frame_ms / 1000.0)
        logger.info(f"[{call_sid}] [BLACKBOX] Finished streaming {chunk_count} chunks.")
    except Exception as e:
        logger.exception(f"[{call_sid}] [BLACKBOX] Error while streaming outbound audio chunks: {e}")

# --- FastAPI Endpoints ---

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
    
    websocket_url = f"wss://{RENDER_EXTERNAL_URL.replace('https://', '')}/media/{call_sid}"
    
    start = Start()
    start.stream(url=websocket_url, track='inbound_track')
    response.append(start)

    # A long pause is crucial to keep the call alive while the WebSocket connects
    # and the agent takes control. The agent's logic will supersede this.
    response.pause(length=60)
    
    logger.info(f"[{call_sid}] Responding with resilient cXML (<Start><Stream>, <Pause>) to URL: {websocket_url}")
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional audio stream between SignalWire and Deepgram."""
    logger.info(f"!!!!!! WebSocket HANDLER ENTRY for call {call_sid}")
    await websocket.accept()
    logger.info(f"🎙️ [BLACKBOX] WebSocket connection accepted for call {call_sid}")

    dg_inbound = deepgram_client.listen.asynclive.v("1")

    inbound_buffer = []
    dg_inbound_ready = asyncio.Event()
    stream_sid = None

    async def produce_and_stream_tts(text_to_speak: str, stream_sid_local: str):
        """Helper function to generate and stream TTS audio."""
        try:
            logger.info(f"[{call_sid}] [BLACKBOX] Starting TTS generation task for text: '{text_to_speak[:30]}...'")
            audio_bytes = await generate_tts_mulaw_bytes_for_stream(text_to_speak, call_sid)
            await send_audio_payload_chunked(websocket, stream_sid_local, audio_bytes, call_sid=call_sid)
            logger.info(f"[{call_sid}] [BLACKBOX] TTS streaming task completed.")
        except Exception as e:
            logger.exception(f"[{call_sid}] [BLACKBOX] Error in produce_and_stream_tts: {e}")

    async def process_and_respond(transcript: str, stream_sid_local: str):
        logger.info(f"[{call_sid}] [BLACKBOX] Starting process_and_respond for transcript: '{transcript}'")
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
            
            logger.info(f"[{call_sid}] [LLM_TRACE] Sending transcript to LLM...")
            chat_completion = await asyncio.to_thread(groq_client.chat.completions.create, messages=messages, model="llama3-8b-8192")
            llm_response_text = chat_completion.choices[0].message.content
            logger.info(f"[{call_sid}] [LLM_TRACE] LLM generated response: '{llm_response_text[:50]}...'")

            conversation_history.append({"role": "user", "content": transcript})
            conversation_history.append({"role": "assistant", "content": llm_response_text})
            redis_client.set(redis_key, json.dumps(conversation_history), ex=3600)

            if llm_response_text:
                logger.info(f"[{call_sid}] [TTS_TRACE] Creating TTS task for response.")
                asyncio.create_task(produce_and_stream_tts(llm_response_text, stream_sid_local))

        except Exception as e:
            logger.error(f"[{call_sid}] [BLACKBOX] An error occurred in process_and_respond.", exc_info=True)
        
        logger.info(f"[{call_sid}] [BLACKBOX] FINISHED processing transcript: '{transcript}'")

    async def on_message(result, **kwargs):
        logger.debug(f"[{call_sid}] Deepgram RAW message: {str(result)}")
        try:
            logger.info(f"[{call_sid}] [DEEPGRAM_TRACE] Received a message from Deepgram.")
            transcript = result.channel.alternatives[0].transcript.strip()
            if not transcript:
                return
        except Exception:
            logger.exception(f"[{call_sid}] Error parsing Deepgram result.")
            return

        speech_final = getattr(result, "speech_final", False) or getattr(result, "is_final", False)

        if transcript and speech_final:
            if not stream_sid:
                logger.warning(f"[{call_sid}] Received final transcript but stream_sid is not yet set. Discarding.")
                return
            logger.info(f"[{call_sid}] Deepgram speech_final received: '{transcript}'")
            asyncio.create_task(process_and_respond(transcript, stream_sid))

    async def on_error(error, **kwargs):
        logger.error(f"[{call_sid}] Deepgram connection error: {error}", exc_info=True)

    dg_inbound.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_inbound.on(LiveTranscriptionEvents.Error, on_error)

    async def start_deepgram_connection():
        try:
            logger.info(f"[{call_sid}] [BLACKBOX] Attempting to start Deepgram connection...")
            await dg_inbound.start(
                model="nova-2-phonecall", language="en-US", encoding="mulaw", sample_rate=8000,
                punctuate=True, smart_format=True, interim_results=True, vad_events=True, endpointing=600
            )
            logger.info(f"[{call_sid}] [BLACKBOX] Deepgram connection STARTED successfully.")
            
            dg_inbound_ready.set()
            logger.info(f"[{call_sid}] [BLACKBOX] Deepgram ready event SET.")
            
            logger.info(f"[{call_sid}] [BLACKBOX] Flushing {len(inbound_buffer)} buffered frames to Deepgram.")
            for chunk in inbound_buffer:
                await dg_inbound.send(chunk)
            inbound_buffer.clear()
            logger.info(f"[{call_sid}] [BLACKBOX] Buffer flushed. Deepgram startup task complete.")

        except Exception as e:
            logger.critical(f"[{call_sid}] [BLACKBOX] CRITICAL ERROR during Deepgram start: {e}", exc_info=True)

    dg_start_task = asyncio.create_task(start_deepgram_connection())

    try:
        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            event = message.get('event')
            
            # This log is too verbose for production, moved to DEBUG level.
            logger.debug(f"[{call_sid}] [BLACKBOX] Received SignalWire message: {json.dumps(message)}")

            if event == 'connected':
                logger.info(f"[{call_sid}] SignalWire WebSocket connected. Protocol: {message.get('protocol', 'N/A')}")
            elif event == 'start':
                stream_sid = message['start'].get('streamSid') if message.get('start') else None
                logger.info(f"[{call_sid}] SignalWire stream started. SID: {stream_sid}")
                # No welcome message will be played. The agent will wait for the user to speak.
            elif event == 'media':
                media = message.get('media', {})
                track = media.get('track')
                payload_b64 = media.get('payload')

                if not payload_b64 or track != 'inbound':
                    continue
                
                try:
                    payload = base64.b64decode(payload_b64)
                except Exception:
                    logger.exception(f"[{call_sid}] Failed to base64-decode media payload.")
                    continue

                if not dg_inbound_ready.is_set():
                    inbound_buffer.append(payload)
                else:
                    await dg_inbound.send(payload)

            elif event == 'stop':
                logger.info(f"[{call_sid}] SignalWire stream stopped. Closing connections.")
                break
            else:
                logger.warning(f"[{call_sid}] Received unknown event from SignalWire: {json.dumps(message)}")
    
    except Exception as e:
        logger.exception(f"[{call_sid}] CRITICAL ERROR in WebSocket handler main loop: {e}")
    finally:
        logger.info(f"[{call_sid}] Cleaning up: finishing Deepgram connection.")
        try:
            await asyncio.sleep(0.1)
            await dg_inbound.finish()
        except Exception:
            logger.exception(f"[{call_sid}] Error while finishing Deepgram connection.")
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"[{call_sid}] WebSocket connection closed for {call_sid}.")
