import numpy as np
import librosa

def pcm_s16_to_float32(audio_np):
    return audio_np.astype(np.float32) / 32768.0

def resample_audio(audio_float32, original_sr, target_sr):
    return librosa.resample(audio_float32, orig_sr=original_sr, target_sr=target_sr)
