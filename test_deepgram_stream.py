import os
import asyncio
import wave
import time
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise RuntimeError("DEEPGRAM_API_KEY is not set in .env file")

AUDIO_FILE = r"C:\Users\ISHAIKH TECHNOLOGIES\Desktop\AIVOICE\public_audio\welcome.wav"
CHUNK_SIZE = 1024  # bytes

async def main():
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
    dg_conn = deepgram.listen.websocket.v("1")

    def on_open(*args, **kwargs):
        print(f"Deepgram OPEN")

    def on_transcript(self, result, **kwargs):
        try:
            alt = result.channel.alternatives[0]
            if alt.transcript:
                print(f"📝 Transcript: {alt.transcript}")
        except Exception as e:
            print(f"Error processing transcript: {e}")

    def on_close(*args, **kwargs): # on_close still uses *args, **kwargs as per main.py fix
        print(f"Deepgram CLOSE")

    def on_error(self, error, **kwargs):
        print(f"Deepgram ERROR: {error}")

    dg_conn.on(LiveTranscriptionEvents.Open, on_open)
    dg_conn.on(LiveTranscriptionEvents.Transcript, on_transcript)
    dg_conn.on(LiveTranscriptionEvents.Close, on_close)
    dg_conn.on(LiveTranscriptionEvents.Error, on_error)

    try:
        dg_conn.start(
            LiveOptions(
                model="nova-3",
                language="en-US",
                encoding="linear16",  # Use linear16 for standard WAV
                sample_rate=44100,     # Use 44100 Hz as detected
                channels=1,
                smart_format=True,
            )
        )
        print(f"Deepgram START requested for {AUDIO_FILE}")

        with wave.open(AUDIO_FILE, 'rb') as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 44100:
                print("Warning: WAV file properties do not match expected (mono, 16-bit, 44100Hz). Deepgram might not transcribe correctly.")
                print(f"File: Channels={wf.getnchannels()}, Sample Width={wf.getsampwidth()}, Frame Rate={wf.getframerate()}")

            while True:
                chunk = wf.readframes(CHUNK_SIZE // wf.getsampwidth()) # Read frames, not bytes directly
                if not chunk:
                    break
                dg_conn.send(chunk)
                await asyncio.sleep(0.02) # Simulate real-time streaming delay

        print("Finished sending audio to Deepgram.")

    except Exception as e:
        print(f"Failed to start or stream to Deepgram: {e}")
    finally:
        if dg_conn:
            await asyncio.sleep(0.5) # Give Deepgram a moment to process last chunks
            dg_conn.finish()
            print("Deepgram FINISH")

if __name__ == "__main__":
    asyncio.run(main())
