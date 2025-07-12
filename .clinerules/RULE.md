ALWAYS USE CONTEX BELOW 200K TOKEN!!!!!!!!!!!!!!!!1 Never guess API parameters – always match official docs.
2. If Groq or SignalWire errors, log the full error and retry with fallback.
3. Optimize all latency bottlenecks: STT, TTS, and Redis calls.
4. System prompt for GROQ should be short, warm, voice-optimized.
5. No hallucinated code. Use real SDK functions only.
6. Claude should not repeat previous code bugs – keep track of fixed errors.
7. Cache: Save Claude response history per call ID in Redis (30-min expiry).
8. Prioritize response quality over length. Use 15–35 word limits.
9. Respect Whisper model size from .env (tiny.en/base.en)
10. YOUR job is to complete and debug entire project until production-ready.