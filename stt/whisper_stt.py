# stt/whisper_stt.py

import logging
import tempfile
import os
from typing import Optional

from faster_whisper import WhisperModel
from app.core.config import (
    STT_LOCAL_PATH,
    STT_DEVICE,
    STT_COMPUTE_TYPE,
    TARGET_STT_SAMPLE_RATE
)
from utils.audio import resample_audio

logger = logging.getLogger(__name__)

class WhisperSTT:
    """Speech-to-Text service using Faster Whisper"""
    
    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.model_path = STT_LOCAL_PATH
        self.device = STT_DEVICE
        self.compute_type = STT_COMPUTE_TYPE
        
    async def initialize(self):
        """Initialize the Faster Whisper model"""
        try:
            logger.info(f"Loading Faster Whisper model: {self.model_path}")
            
            self.model = WhisperModel(
                self.model_path,
                device=self.device,
                compute_type=self.compute_type
            )
            
            logger.info("Faster Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize STT service: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data to text
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            str: Transcribed text or None if transcription failed
        """
        try:
            if not self.model:
                logger.error("STT model not initialized")
                return None
            
            if not audio_data:
                logger.warning("Empty audio data provided")
                return None
            
            # Save audio to temporary file for Whisper processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Resample audio if needed
                resampled_audio = resample_audio(audio_data, TARGET_STT_SAMPLE_RATE)
                
                temp_file.write(resampled_audio)
                temp_file.flush()
            
            try:
                # Transcribe using Faster Whisper
                segments, info = self.model.transcribe(
                    temp_path,
                    language="en",
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    condition_on_previous_text=False
                )
                
                # Combine all segments into single transcript
                transcript_parts = []
                for segment in segments:
                    transcript_parts.append(segment.text.strip())
                
                transcript = " ".join(transcript_parts).strip()
                
                if transcript:
                    logger.info(f"Transcription successful: '{transcript}'")
                    return transcript
                else:
                    logger.warning("Empty transcription result")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def transcribe_file(self, file_path: str) -> Optional[str]:
        """Transcribe audio file to text
        
        Args:
            file_path: Path to audio file
            
        Returns:
            str: Transcribed text or None if transcription failed
        """
        try:
            if not self.model:
                logger.error("STT model not initialized")
                return None
            
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return None
            
            # Transcribe using Faster Whisper
            segments, info = self.model.transcribe(
                file_path,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # Combine all segments
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text.strip())
            
            transcript = " ".join(transcript_parts).strip()
            
            if transcript:
                logger.info(f"File transcription successful: '{transcript}'")
                return transcript
            else:
                logger.warning("Empty transcription result from file")
                return None
                
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return None
    
    async def cleanup(self):
        """Clean up STT resources"""
        try:
            self.model = None
            logger.info("STT service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during STT cleanup: {e}")