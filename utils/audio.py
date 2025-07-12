# utils/audio.py
import audioop
import numpy as np
from typing import Union

def decode_twilio_mulaw(payload_bytes: bytes) -> np.ndarray:
    """Decode Twilio/SignalWire μ-law encoded audio to PCM S16."""
    pcm_data_bytes = audioop.ulaw2lin(payload_bytes, 2)
    return np.frombuffer(pcm_data_bytes, dtype=np.int16)

def pcm_s16_to_float32(pcm_s16: np.ndarray) -> np.ndarray:
    """Convert PCM S16 audio to float32 format (range -1.0 to 1.0)."""
    return pcm_s16.astype(np.float32) / 32768.0

def float32_to_pcm_s16(float32_audio: np.ndarray) -> np.ndarray:
    """Convert float32 audio (range -1.0 to 1.0) to PCM S16 format."""
    return (float32_audio * 32768.0).astype(np.int16)

def encode_twilio_mulaw(pcm_s16_bytes: bytes) -> bytes:
    """Encode PCM S16 audio to Twilio/SignalWire μ-law format."""
    return audioop.lin2ulaw(pcm_s16_bytes, 2)

def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    """Resample audio from source_rate to target_rate."""
    if source_rate == target_rate:
        return audio
    
    # Convert to bytes for audioop
    if audio.dtype == np.float32:
        audio_bytes = float32_to_pcm_s16(audio).tobytes()
    else:
        audio_bytes = audio.tobytes()
    
    # Resample using audioop
    resampled_bytes, _ = audioop.ratecv(
        audio_bytes, 2, 1, source_rate, target_rate, None
    )
    
    # Convert back to numpy array
    resampled = np.frombuffer(resampled_bytes, dtype=np.int16)
    
    # If input was float32, convert back to float32
    if audio.dtype == np.float32:
        resampled = pcm_s16_to_float32(resampled)
    
    return resampled