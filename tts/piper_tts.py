# tts/piper_tts.py

import logging
import tempfile
import os
from typing import Optional
import numpy as np

from app.core.config import (
    PIPER_MODEL_PATH,
    PIPER_CONFIG_PATH
)

logger = logging.getLogger(__name__)

class PiperTTS:
    """Text-to-Speech service using Piper"""
    
    def __init__(self):
        self.model = None
        self.model_path = PIPER_MODEL_PATH
        self.config_path = PIPER_CONFIG_PATH
        
    async def initialize(self):
        """Initialize the Piper TTS model"""
        try:
            # Import here to avoid loading the model until needed
            from piper import PiperVoice
            
            logger.info(f"Loading Piper TTS model: {self.model_path}")
            
            self.model = PiperVoice.load(self.model_path, config_path=self.config_path)
            
            logger.info("Piper TTS model loaded successfully")
            
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize PiperTTS service: {e}. The service will be disabled.")
            self.model = None # Ensure model is None so it's flagged as non-operational
            # Do not re-raise the exception, to allow the main application to continue running.

    def initialize_sync(self):
        """Synchronously initialize the Piper TTS model for use in Celery workers."""
        try:
            from piper import PiperVoice
            logger.info(f"Loading Piper TTS model synchronously: {self.model_path}")
            self.model = PiperVoice.load(self.model_path, config_path=self.config_path)
            logger.info("Piper TTS model loaded successfully (sync).")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize PiperTTS service (sync): {e}.")
            self.model = None

    def text_to_speech_sync(self, text: str) -> Optional[bytes]:
        """Synchronously convert text to speech audio data."""
        if not self.model:
            logger.error("TTS model not initialized (sync).")
            return None
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS (sync).")
            return None
            
        try:
            # The updated synthesize method returns audio bytes directly.
            logger.info(f"Converting to speech (sync)...")
            audio_bytes = self.model.synthesize(text)
            logger.info(f"Piper audio generated (sync): {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            logger.error(f"Error with Piper TTS (sync): {e}", exc_info=True)
            return None
    
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech audio data
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bytes: Audio data in WAV format or None if conversion failed
        """
        if not self.model:
            logger.error("TTS model not initialized")
            return None
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return None
            
        try:
            # The updated synthesize method returns audio bytes directly.
            logger.info(f"Converting to speech...")
            audio_bytes = self.model.synthesize(text)
            logger.info(f"Piper audio generated: {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            logger.error(f"Error with Piper TTS: {e}", exc_info=True)
            return None
    
    async def cleanup(self):
        """Clean up TTS resources"""
        try:
            self.model = None
            logger.info("TTS service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during TTS cleanup: {e}")
