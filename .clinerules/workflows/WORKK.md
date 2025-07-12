ALWAYS USE API REQUEST CONTEXT BELOW 200K TOKENS
You are now my elite coding agent helping develop a $100M-quality AI Voice Agent SaaS (AuraVoice). Your task is to **complete, debug, and productionize** the entire project step by step using the existing source code and public documentation.

🧠 **Context:**
This is a real-time AI voice agent (like OpenAI Voice Mode) that:
- Answers calls via SignalWire Relay SDK (Python)
- Uses GROQ STT Whisper STT (via Groq or Faster-Whisper)
- Replies via GROQ API LLM
- Speaks via GROQ TTS or fallback PIPER TTS
- Uses Redis + Celery to handle 10–50 concurrent calls
- Target is Oracle Free Tier / Fly.io for free-tier hosting

🎯 **GOALS:**
- Complete the entire AI voice agent pipeline (call → listen → transcribe → reply → speak) without errors
- Debug **each line** of code using:
  - [SignalWire Relay Python SDK Docs](https://docs.signalwire.com/reference/relay-sdk-python/v2/)
  - [Groq API Docs](https://console.groq.com/docs)
  - [Redis Python Docs](https://redis.readthedocs.io/en/stable/)
  - [Celery Docs](https://docs.celeryq.dev/en/stable/)