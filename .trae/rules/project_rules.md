emini Agent Instructions (AuraVoice AI Voice Agent Project)

As an advanced world-class coding agent, you must follow this protocol when working on this project:

---

## 🧠 OVERVIEW

This project is a **real-time AI voice agent** ("AuraVoice") that answers phone calls using SignalWire, listens to speech, transcribes it using Whisper, generates AI responses via Groq LLM, and speaks back using Piper TTS. It uses **Celery** with **Redis** to process audio asynchronously while maintaining system responsiveness.

> 🎯 **GOAL**: Build a fully conversational, context-aware AI phone agent (like OpenAI Voice Mode) deployed on Oracle Free Tier, Fly.io, or Docker — fast, humanlike, and production-ready.

---

## 📂 PROJECT STRUCTURE + CODE RELATION MAP

/AIVOICE/
│
├── app/
│ ├── relay_server.py # ✅ SignalWire consumer: accepts calls, collects speech via VAD, sends to Celery
│ ├── core/
│ │ └── config.py # Environment and AI model paths, API keys
│ └── utils/
│ └── audio.py # Audio decoding, resampling (mu-law, PCM, etc.)
│
├── celery_worker/
│ ├── celery_app.py # ✅ Celery setup with Redis broker/backend
│ └── tasks.py # ✅ Core AI pipeline: STT → LLM → TTS → Base64 return
│
├── models/ # Whisper + Piper model files (tiny.en, lessac-medium.onnx, etc.)
├── .env # SignalWire + Groq API keys, model paths
└── requirements.txt # All dependencies: signalwire, celery, faster-whisper, groq, piper, redis

yaml
Copy
Edit

---

## 🧠 STACK FLOW (VAD Mode)

📞 Incoming call →
🎤 User speaks →
🎙️ SignalWire detects speech via prompt_tts() →
🌐 Recording URL sent to Celery →
🧠 Celery task transcribes with Whisper →
🗣️ Generates reply via Groq →
🧏 Synthesizes speech via Piper →
🔁 Played back to user → Repeat

markdown
Copy
Edit

---

## ✅ BEHAVIORAL RULES FOR GEMINI AGENT

1. **📚 Docs First**: Always check latest [SignalWire Python SDK Docs](https://docs.signalwire.com/reference/relay-sdk-python/v2/), [Celery Docs](https://docs.celeryq.dev/), [Redis Python Client](https://redis.readthedocs.io/), and [Groq Chat API](https://console.groq.com/docs).

2. **🧩 Connected File Analysis**: When modifying or debugging any code:
   - Check all related files (`relay_server.py`, `tasks.py`, `celery_app.py`, `audio.py`)
   - Understand class ↔ function ↔ task flow
   - Avoid changing a file in isolation

3. **🎯 Ensure**:
   - `relay_server.py` handles call flow via `CallHandler`
   - `tasks.py` uses preloaded AI models to return audio bytes
   - Redis/Celery are running in background (via Docker Compose)
   - `.env` is correctly sourced in all entry points
   - Audio is processed using `prompt_tts()` with `speech_end_timeout` for VAD-style detection

4. **💡 When Given an Error**:
   - Trace the stack fully
   - Identify where the bug impacts: `relay`, `celery`, or `audio`
   - Suggest and apply clean fixes

---

## ✅ ADVANCED FEATURES TO ADD

You will be asked to add:
- ✅ **Conversation memory** using Redis (save history per call ID or phone number)
- ✅ **Intent classification / sentiment detection**
- ✅ **Multi-turn awareness** (context trim & inject past messages)
- ✅ **Auto language switching for Whisper**
- ✅ **Session logs + transcripts per caller**
- ✅ **User memory across calls (via `call.from_number`)**

---

## 🐳 REDIS + CELERY VIA DOCKER (Optional)

To run Redis and Celery using Docker on Oracle Free Tier:

```bash
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis
    ports:
      - "6379:6379"
  celery:
    build: .
    command: celery -A celery_worker.celery_app worker --loglevel=info
    depends_on:
      - redis
🧠 CONTEXTUAL LLM MEMORY FORMAT (Example)
python
Copy
Edit
messages = [
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Where is my order?"},
  {"role": "assistant", "content": "Let me check that for you."},
  {"role": "user", "content": "It was supposed to arrive yesterday."}
]
✅ WHEN TUNING FOR PROD
Whisper tiny.en → medium / distil-small.en

LLM → LLaMA3-70B or mixtral on Groq

Piper → speaker embedding or custom voice

Cache model loads in worker_process_init only

💰 VISION (100M+ SaaS)
Build an open-source, production-ready AI call agent that:

Takes phone orders

Books appointments

Handles support calls

Learns from caller tone

Remembers users

Speaks like a human

✅ FINAL CHECKLIST FOR GEMINI
Before accepting code:

 Confirm SignalWire SDK method usage is 100% correct

 Ensure async methods are properly awaited

 Confirm Celery worker is connected to Redis and processing jobs

 Check AI models are preloaded (not loaded per task)

 Inspect return types: TTS output must be proper PCM or µ-law

 Add .get() timeout guard to all Celery response fetches