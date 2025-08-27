import asyncio
import wave
import audioop
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# Your API Key
DEEPGRAM_API_KEY = "ab3f033e8497670371a4f17664a3ad3743a41858"
AUDIO_FILE = r"C:\Users\ISHAIKH TECHNOLOGIES\Desktop\AIVOICE\public_audio\welcome.wav"

async def main():
    dg = DeepgramClient(DEEPGRAM_API_KEY)
    conn = dg.listen.websocket.v("1")

    # ----------------------
    # Event Handlers
    # ----------------------
    def on_open(event, **kwargs):
        print("✅ Connection opened")

    def on_transcript(event, **kwargs):
        try:
            text = event.channel.alternatives[0].transcript
            if text.strip():
                print("Transcript:", text)
        except Exception:
            pass

    def on_close(event, **kwargs):
        print("⏹ Connection closed")

    def on_error(event, **kwargs):
        print("❌ Error:", event)

    # Register Handlers (must pass function + not decorator!)
    conn.on(LiveTranscriptionEvents.Open, on_open)
    conn.on(LiveTranscriptionEvents.Transcript, on_transcript)
    conn.on(LiveTranscriptionEvents.Close, on_close)
    conn.on(LiveTranscriptionEvents.Error, on_error)

    # ----------------------
    # Start Transcription
    # ----------------------
    opts = LiveOptions(
        model="nova-2",
        language="en-US",
        encoding="linear16",
        sample_rate=16000,
        interim_results=False,
        punctuate=True
    )
    conn.start(opts)

    # ----------------------
    # Read & Send WAV Audio
    # ----------------------
    wf = wave.open(AUDIO_FILE, "rb")
    raw = wf.readframes(wf.getnframes())
    wf.close()

    if wf.getframerate() != 16000:
        raw, _ = audioop.ratecv(raw, wf.getsampwidth(), wf.getnchannels(),
                                wf.getframerate(), 16000, None)

    # Send in chunks (simulate live stream)
    chunk_size = 3200  # ~0.1s audio
    for i in range(0, len(raw), chunk_size):
        conn.send(raw[i:i+chunk_size])
        await asyncio.sleep(0.1)

    conn.finish()
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
