import wave
import sys
import os

def get_wav_info(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        with wave.open(file_path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            duration = nframes / float(framerate)

            print(f"File: {file_path}")
            print(f"Channels: {channels}")
            print(f"Sample Width (bytes): {sample_width}")
            print(f"Frame Rate (Hz): {framerate}")
            print(f"Number of Frames: {nframes}")
            print(f"Duration (seconds): {duration:.2f}")

            # Infer encoding based on sample width
            encoding = "linear16" if sample_width == 2 else "unknown"
            print(f"Inferred Encoding: {encoding} (assuming PCM for 16-bit)")

    except wave.Error as e:
        print(f"Error reading WAV file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    audio_file_path = r"C:\Users\ISHAIKH TECHNOLOGIES\Desktop\AIVOICE\public_audio\welcome.wav"
    get_wav_info(audio_file_path)
