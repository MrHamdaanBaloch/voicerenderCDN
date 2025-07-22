import torch
import logging
import io

logger = logging.getLogger("VADService")

class VADDetector:
    _model = None
    _utils = None

    def __init__(self):
        if VADDetector._model is None:
            try:
                logger.info("Loading Silero VAD model...")
                model, utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False
                )
                VADDetector._model = model
                VADDetector._utils = utils
                logger.info("Silero VAD model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Silero VAD model: {e}", exc_info=True)
                raise

    def is_speech(self, audio_bytes: bytes) -> bool:
        """
        Checks if a raw audio byte string contains speech.
        """
        if not self._model or not self._utils:
            logger.error("VAD model is not loaded.")
            return False

        (get_speech_timestamps, _, read_audio, *_) = self._utils
        
        try:
            # Use an in-memory buffer to read the audio bytes
            audio_buffer = io.BytesIO(audio_bytes)
            wav = read_audio(audio_buffer, sampling_rate=8000)
            # Lower the speech probability threshold to make the VAD more sensitive.
            # The default is 0.5, which is too strict for this use case.
            speech_timestamps = get_speech_timestamps(
                wav, 
                self._model, 
                sampling_rate=8000,
                speech_prob_threshold=0.35
            )
            
            if len(speech_timestamps) > 0:
                logger.info("Speech detected in audio.")
                return True
            else:
                logger.info("No speech detected in audio.")
                return False
        except Exception as e:
            logger.error(f"VAD analysis failed: {e}", exc_info=True)
            return True # Default to assuming speech on error
