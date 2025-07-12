# vad/vad_detector.py
import webrtcvad
import numpy as np
from typing import List, Tuple

class VoiceActivityDetector:
    def __init__(self, sample_rate: int = 8000, frame_duration_ms: int = 30, aggressiveness: int = 3):
        """
        Initialize the WebRTC VAD detector.
        
        Args:
            sample_rate: Audio sample rate in Hz (8000, 16000, 32000, or 48000)
            frame_duration_ms: Frame duration in milliseconds (10, 20, or 30)
            aggressiveness: VAD aggressiveness mode (0-3), higher is more aggressive
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.vad = webrtcvad.Vad(aggressiveness)
        
        # Calculate frame size based on sample rate and frame duration
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
    def is_speech(self, audio_frame: bytes) -> bool:
        """
        Detect if a frame contains speech.
        
        Args:
            audio_frame: PCM audio frame (must be 16-bit mono)
            
        Returns:
            True if speech is detected, False otherwise
        """
        try:
            return self.vad.is_speech(audio_frame, self.sample_rate)
        except Exception as e:
            print(f"VAD error: {e}")
            return False
    
    def process_audio(self, audio: np.ndarray, padding_ms: int = 300) -> List[Tuple[np.ndarray, bool]]:
        """
        Process audio and return segments with speech/non-speech labels.
        
        Args:
            audio: PCM S16 audio as numpy array
            padding_ms: Padding in milliseconds to add around speech segments
            
        Returns:
            List of tuples containing (audio_segment, is_speech)
        """
        # Convert to bytes if needed
        if isinstance(audio, np.ndarray):
            audio_bytes = audio.tobytes()
        else:
            audio_bytes = audio
            
        # Split audio into frames
        frames = []
        for i in range(0, len(audio_bytes) - self.frame_size + 1, self.frame_size):
            frames.append(audio_bytes[i:i + self.frame_size])
            
        # Detect speech in each frame
        speech_frames = [self.is_speech(frame) for frame in frames]
        
        # Group consecutive frames with the same label
        segments = []
        current_segment = []
        current_label = speech_frames[0] if speech_frames else False
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech == current_label:
                current_segment.append(i)
            else:
                # Add padding frames to speech segments
                if current_label:
                    padding_frames = int(padding_ms / self.frame_duration_ms)
                    start_idx = max(0, current_segment[0] - padding_frames)
                    end_idx = min(len(frames), current_segment[-1] + 1 + padding_frames)
                    segment_bytes = b''.join(frames[start_idx:end_idx])
                else:
                    segment_bytes = b''.join([frames[j] for j in current_segment])
                    
                segments.append((np.frombuffer(segment_bytes, dtype=np.int16), current_label))
                
                current_segment = [i]
                current_label = is_speech
                
        # Add the last segment
        if current_segment:
            if current_label:
                padding_frames = int(padding_ms / self.frame_duration_ms)
                start_idx = max(0, current_segment[0] - padding_frames)
                end_idx = min(len(frames), current_segment[-1] + 1 + padding_frames)
                segment_bytes = b''.join(frames[start_idx:end_idx])
            else:
                segment_bytes = b''.join([frames[j] for j in current_segment])
                
            segments.append((np.frombuffer(segment_bytes, dtype=np.int16), current_label))
            
        return segments