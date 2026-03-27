import logging
import os
import asyncio
import json
import uuid
import base64
import redis
import aiofiles
from fastapi import FastAPI, WebSocket, Response, Request, Depends, HTTPException
from starlette.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import websockets
from sqlalchemy.orm import Session
from groq import Groq
from dotenv import load_dotenv
from signalwire.voice_response import VoiceResponse, Start
from twilio.twiml.voice_response import VoiceResponse as TwilioVoiceResponse
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions

# --- Import Database Logic ---
from app.database import get_db, SessionLocal
from app.models import User, Organization, Agent, Call, Transcript
from app.api.endpoints import router as api_router # Import the API router

# --- Load Environment Variables & Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VoiceAgentService")

# --- FastAPI App Setup ---
app = FastAPI()

# Include the API router
app.include_router(api_router)

# --- CORS Middleware (Fixed for Local Frontend & Preflight) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://voicerender.vercel.app", "https://aura-voice-five.vercel.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Configuration & Clients ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PUBLIC_URL_BASE = os.environ.get("PUBLIC_URL_BASE")

TELEPHONY_CODEC = "pcm_mulaw"
OPTIMIZED_AUDIO_DIR = "public_audio"
RAW_AUDIO_DIR = "temp_raw_audio"

groq_client = Groq(api_key=GROQ_API_KEY)
dg_config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY, dg_config)
redis_client = redis.from_url(os.environ["REDIS_URL"])

# --- Directory Setup ---
for directory in [RAW_AUDIO_DIR, OPTIMIZED_AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.mount("/audio", StaticFiles(directory=OPTIMIZED_AUDIO_DIR), name="audio")

# --- Helper Functions ---

def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {path}: {e}")

# --- Legacy Helpers Deleted ---
# generate_tts_mulaw_bytes_for_stream has been replaced with in-memory direct WS streaming.

# --- API Endpoints ---

@app.get("/")
async def root():
    return {"status": "success", "message": "Voice Agent Service with Database is running."}
from app.core.webhook_security import verify_twilio_signature, verify_signalwire_signature

@app.post("/incoming_call")
async def handle_incoming_call(request: Request, db: Session = Depends(get_db)):
    body_bytes = await request.body()
    if not verify_signalwire_signature(request, body_bytes):
        raise HTTPException(status_code=403, detail="Invalid signature")

    body = await request.form()
    call_sid = body.get("CallSid")
    to_number = body.get("To")
    from_number = body.get("From")
    
    # Try to find agent by phone number, otherwise get the first active one
    agent = db.query(Agent).filter(Agent.signalwire_phone_number == to_number, Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).filter(Agent.is_active == True).first()
        
    response = VoiceResponse()

    if not agent:
        logger.error("No active agent found for incoming call")
        response.say("We're sorry, this agent is currently offline.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Check Prepaid Balance
    if agent.organization.balance_seconds <= 0:
        logger.warning(f"Org {agent.organization_id} has insufficient balance. Rejecting call {call_sid}.")
        response.say("This agent is currently unavailable due to insufficient account balance. Please contact the administrator.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Create the Call record
    new_call = Call(
        agent_id=agent.id,
        organization_id=agent.organization_id,
        call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        status="in_progress"
    )
    db.add(new_call)
    db.commit()

    base_url = RENDER_EXTERNAL_URL
    ws_protocol = "wss" if base_url.startswith("https") else "ws"
    clean_url = base_url.replace('https://', '').replace('http://', '')
    websocket_url = f"{ws_protocol}://{clean_url}/media/{call_sid}"
    
    start = Start()
    start.stream(url=websocket_url, track='both_tracks')
    response.append(start)
    response.pause(length=60)
    return Response(content=str(response), media_type="application/xml")

@app.post("/incoming_twilio")
async def handle_incoming_twilio(request: Request, db: Session = Depends(get_db)):
    """BYOC Endpoint for Twilio clients"""
    body_bytes = await request.body()
    if not verify_twilio_signature(request, body_bytes):
        raise HTTPException(status_code=403, detail="Invalid signature")

    body = await request.form()
    call_sid = body.get("CallSid")
    to_number = body.get("To")
    from_number = body.get("From")
    
    agent = db.query(Agent).filter(Agent.signalwire_phone_number == to_number, Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).filter(Agent.is_active == True).first()
        
    response = TwilioVoiceResponse()

    if not agent:
        logger.error("No active agent found for Twilio incoming call")
        response.say("We're sorry, this agent is currently offline.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    if agent.organization.balance_seconds <= 0:
        logger.warning(f"Org {agent.organization_id} has insufficient balance. Rejecting Twilio call {call_sid}.")
        response.say("This agent is currently unavailable due to insufficient account balance. Please contact the administrator.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    new_call = Call(
        agent_id=agent.id,
        organization_id=agent.organization_id,
        call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        status="in_progress"
    )
    db.add(new_call)
    db.commit()

    base_url = RENDER_EXTERNAL_URL
    ws_protocol = "wss" if base_url.startswith("https") else "ws"
    clean_url = base_url.replace('https://', '').replace('http://', '')
    websocket_url = f"{ws_protocol}://{clean_url}/media/{call_sid}"
    
    connect = response.connect()
    connect.stream(url=websocket_url, track='both_tracks')
    
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media/{call_sid}")
async def media_websocket_handler(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    stream_sid = None
    
    # Internal communication flows
    llm_input_queue = asyncio.Queue()
    tts_input_queue = asyncio.Queue()

    # Tasks and states
    llm_task = None
    tts_task = None
    dg_stt_connection = None
    is_answering = False

    db = SessionLocal()
    call_record = db.query(Call).filter(Call.call_sid == call_sid).first()
    
    if not call_record:
        logger.error(f"Rejecting WS - Call {call_sid} not found in DB.")
        await websocket.close()
        db.close()
        return

    # Grab Agent Prompt
    agent_prompt = "You are a friendly, conversational AI assistant on a phone call. Keep answers extremely brief, natural, and direct. Do not use markdown."
    if call_record.agent and call_record.agent.system_prompt:
        agent_prompt = call_record.agent.system_prompt

    # --- Worker 1: Groq LLM Generation Stream ---
    async def llm_worker():
        nonlocal is_answering
        while True:
            try:
                user_text = await llm_input_queue.get()
                if not user_text.strip():
                    continue
                    
                is_answering = True
                
                # Save purely for logging
                try:
                    t = Transcript(call_id=call_record.id, speaker="user", text=user_text)
                    db.add(t)
                    db.commit()
                except Exception:
                    db.rollback()

                logger.info(f"[LLM] Inferencing for user input: {user_text}")
                
                # Inference to Groq LLM
                stream = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": agent_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    stream=True,
                    max_tokens=150
                )
                
                ai_full_text = ""
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        ai_full_text += content
                        # Stream the words directly into the TTS engine queue
                        await tts_input_queue.put(content)
                
                # Flush instruction to Deepgram Aura
                await tts_input_queue.put("\n\n")

                # Save agent transcript
                try:
                    t = Transcript(call_id=call_record.id, speaker="agent", text=ai_full_text)
                    db.add(t)
                    db.commit()
                except Exception:
                    db.rollback()

            except Exception as e:
                logger.error(f"[LLM] Error: {e}")
            finally:
                is_answering = False

    # --- Worker 2: Deepgram Aura-1 TTS Stream ---
    async def tts_worker():
        tts_url = "wss://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=mulaw&sample_rate=8000"
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        
        while True:
            try:
                async with websockets.connect(tts_url, extra_headers=headers) as tts_ws:
                    
                    # Sub-task to receive mulaw bytes from Deepgram Aura and blast them to the Phone
                    async def receive_tts_audio():
                        while True:
                            try:
                                message = await tts_ws.recv()
                                if isinstance(message, bytes) and stream_sid:
                                    payload = base64.b64encode(message).decode("utf-8")
                                    await websocket.send_text(json.dumps({
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {"track": "outbound", "payload": payload}
                                    }))
                            except websockets.exceptions.ConnectionClosed:
                                break
                            except Exception as e:
                                logger.error(f"[TTS] Receive error: {e}")
                                break
                                
                    recv_task = asyncio.create_task(receive_tts_audio())
                    
                    # Main loop streaming text characters TO Deepgram Aura
                    while True:
                        text_chunk = await tts_input_queue.get()
                        
                        try:
                            if text_chunk == "\n\n":
                                await tts_ws.send(json.dumps({"type": "Flush"}))
                            else:
                                await tts_ws.send(json.dumps({"type": "Speak", "text": text_chunk}))
                        except Exception as e:
                            logger.error(f"[TTS] Send Error: {e}")
                            break
                            
            except Exception as e:
                logger.error(f"[TTS] Websocket Connection Error: {e}")
                await asyncio.sleep(1) # Reconnect delay

    # --- Start Workers ---
    llm_task = asyncio.create_task(llm_worker())
    tts_task = asyncio.create_task(tts_worker())

    # --- Configure Deepgram Flux STT (Listening & Interruption) ---
    async def start_deepgram_stt():
        nonlocal dg_stt_connection
        try:
            dg_stt_connection = deepgram_client.listen.asynclive.v("1")

            async def on_message(self, result, **kwargs):
                if result.type == "Results" and result.is_final:
                    transcript_text = result.channel.alternatives[0].transcript
                    if transcript_text:
                        # Feed recognized text into LLM queue
                        await llm_input_queue.put(transcript_text)
            
            async def on_speech_started(self, speech_started, **kwargs):
                nonlocal is_answering
                # The user interrupted the AI mid-sentence!
                if is_answering and stream_sid:
                    logger.info("[VAD] Interruption Detected! Stopping AI Audio.")
                    # 1. Clear the phone buffer
                    await websocket.send_text(json.dumps({
                        "event": "clear",
                        "streamSid": stream_sid
                    }))
                    
                    # 2. Flush the TTS queue to stop sending remaining text
                    while not tts_input_queue.empty():
                        tts_input_queue.get_nowait()
                        
                    is_answering = False

            dg_stt_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_stt_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)

            # Deepgram Flux Model optimized for conversational end-of-turn
            options = LiveOptions(
                model="flux", 
                language="en-US", 
                encoding="mulaw", 
                sample_rate=8000,
                interim_results=False, 
                vad_events=True,       # Required for SpeechStarted
                endpointing=300
            )
            await dg_stt_connection.start(options)
        except Exception as e:
            logger.error(f"[STT] Deepgram Setup Error: {e}")

    # Launch STT
    stt_task = asyncio.create_task(start_deepgram_stt())

    # --- Telephony WebSocket Loop (Twilio/SignalWire) ---
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get('event')

            if event == 'start':
                stream_sid = data['start']['streamSid']
                logger.info(f"[Telephony] Stream connected: {stream_sid}")
                
                # Initial greeting push
                greeting = "Hello! Welcome to the voice agent."
                await tts_input_queue.put(greeting)
                await tts_input_queue.put("\n\n")

            elif event == 'media':
                media = data.get('media', {})
                if media.get('track') == 'inbound':
                    audio_bytes = base64.b64decode(media.get('payload'))
                    # Send bytes to Deepgram STT
                    if dg_stt_connection:
                        await dg_stt_connection.send(audio_bytes)
            
            elif event == 'stop':
                logger.info(f"[Telephony] Stream stopped: {stream_sid}")
                break
    except Exception as e:
        logger.error(f"[Telephony] Loop Error: {e}")
    finally:
        # Cleanup routine
        if dg_stt_connection:
            await dg_stt_connection.finish()
        if stt_task: stt_task.cancel()
        if llm_task: llm_task.cancel()
        if tts_task: tts_task.cancel()
        
        await websocket.close()
        
        # Complete call in billing system
        if call_record:
            try:
                from datetime import datetime
                call_record.status = "completed"
                call_record.end_time = datetime.utcnow()
                call_record.duration_seconds = (call_record.end_time - call_record.start_time).seconds
                
                if call_record.organization:
                    org = call_record.organization
                    org.balance_seconds = max(0, org.balance_seconds - call_record.duration_seconds)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to update billing: {e}")
                db.rollback()
        db.close()
