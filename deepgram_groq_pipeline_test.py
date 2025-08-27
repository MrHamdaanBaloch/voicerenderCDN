import os
import asyncio
import wave
import json
import queue # Import the standard queue module
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from groq import Groq

# -------------------------------
# Setup & Config
# -------------------------------
load_dotenv()

# Deepgram API Key
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise RuntimeError("DEEPGRAM_API_KEY is not set in .env file")

# Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in .env file")

# Audio file to simulate live stream
AUDIO_FILE = r"C:\Users\ISHAIKH TECHNOLOGIES\Desktop\AIVOICE\public_audio\welcome.wav"
# Audio properties (from previous analysis of welcome.wav)
AUDIO_SAMPLE_RATE = 44100
AUDIO_ENCODING = "linear16" # 16-bit PCM
AUDIO_CHANNELS = 1
CHUNK_SIZE = 1024 # bytes

# Initialize clients
deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Queue to hold transcripts for Groq processing (thread-safe for Deepgram thread)
transcript_queue = queue.Queue()

# -------------------------------
# Deepgram Event Handlers
# -------------------------------
def on_deepgram_open(self, *args, **kwargs):
    print(f"Deepgram OPEN")

def on_deepgram_transcript(self, result, **kwargs):
    try:
        alt = result.channel.alternatives[0]
        if alt.transcript:
            print(f"📝 Deepgram Transcript: {alt.transcript}")
            # Put the transcript into the thread-safe queue
            transcript_queue.put(alt.transcript)
    except Exception as e:
        print(f"Error processing Deepgram transcript: {e}")

def on_deepgram_error(self, error, **kwargs):
    print(f"Deepgram ERROR: {error}")

def on_deepgram_close(self, *args, **kwargs):
    print(f"Deepgram CLOSE")

# -------------------------------
# Main Pipeline Functions
# -------------------------------
async def stream_audio_to_deepgram(dg_connection):
    """
    Reads a pre-recorded WAV file and streams it to Deepgram.
    """
    try:
        with wave.open(AUDIO_FILE, 'rb') as wf:
            if wf.getnchannels() != AUDIO_CHANNELS or \
               wf.getsampwidth() != (16 // 8) or \
               wf.getframerate() != AUDIO_SAMPLE_RATE:
                print(f"Warning: WAV file properties ({wf.getnchannels()}ch, {wf.getsampwidth()*8}-bit, {wf.getframerate()}Hz) "
                      f"do not match expected ({AUDIO_CHANNELS}ch, 16-bit, {AUDIO_SAMPLE_RATE}Hz). "
                      "Deepgram might not transcribe correctly.")

            while True:
                chunk = wf.readframes(CHUNK_SIZE // wf.getsampwidth())
                if not chunk:
                    break
                dg_connection.send(chunk)
                await asyncio.sleep(0.02) # Simulate real-time streaming delay

        print("Finished sending audio to Deepgram.")

    except Exception as e:
        print(f"Failed to stream audio to Deepgram: {e}")
    finally:
        if dg_connection:
            await asyncio.sleep(0.5) # Give Deepgram a moment to process last chunks
            dg_connection.finish()
            print("Deepgram FINISH called.")

async def process_transcripts_with_groq():
    """
    Continuously pulls transcripts from the thread-safe queue and sends them to Groq.
    """
    print("Groq processing task started.")
    while True:
        try:
            transcript = transcript_queue.get_nowait()
            if transcript is None: # Sentinel value to stop the task
                print("Groq task: Received stop signal.")
                break

            print(f"Sending to Groq: '{transcript}'")
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": transcript,
                        }
                    ],
                    model="llama3-8b-8192", # Or another suitable Groq model
                )
                groq_response = chat_completion.choices[0].message.content
                print(f"🤖 Groq Response: {groq_response}\n")
            except Exception as e:
                print(f"Error getting Groq response: {e}")
            finally:
                transcript_queue.task_done() # Mark as done even if Groq fails
        except queue.Empty:
            await asyncio.sleep(0.1) # Wait a bit if queue is empty
            continue
        except Exception as e:
            print(f"Error in Groq processing task: {e}")

async def main():
    # Deepgram live connection setup
    dg_connection = deepgram_client.listen.websocket.v("1")

    dg_connection.on(LiveTranscriptionEvents.Open, on_deepgram_open)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_deepgram_transcript)
    dg_connection.on(LiveTranscriptionEvents.Error, on_deepgram_error)
    dg_connection.on(LiveTranscriptionEvents.Close, on_deepgram_close)

    try:
        dg_connection.start(
            LiveOptions(
                model="nova-3",
                language="en-US",
                encoding=AUDIO_ENCODING,
                sample_rate=AUDIO_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                smart_format=True,
                interim_results=False # Only get final transcripts
            )
        )
        print(f"Deepgram START requested for {AUDIO_FILE}")

        # Create tasks for streaming audio and processing transcripts
        audio_stream_task = asyncio.create_task(stream_audio_to_deepgram(dg_connection))
        groq_process_task = asyncio.create_task(process_transcripts_with_groq())

        # Wait for the audio streaming to complete
        await audio_stream_task

        # Signal the Groq processing task to stop after all transcripts are processed
        # No need for transcript_queue.join() with queue.Queue, just send sentinel
        transcript_queue.put(None) # Send sentinel to stop Groq task
        await groq_process_task # Wait for Groq task to finish

    except Exception as e:
        print(f"Main pipeline error: {e}")
    finally:
        if dg_connection:
            try:
                await asyncio.sleep(0.05)
                dg_connection.finish()
            except Exception as e:
                print(f"Error during Deepgram connection finish: {e}")

if __name__ == "__main__":
    asyncio.run(main())
