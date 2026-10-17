"""Local Speech-to-Text transcriber using Faster-Whisper."""

import logging
from typing import Optional
import numpy as np
from faster_whisper import WhisperModel
from src.core.config import STTConfig, config

logger = logging.getLogger(__name__)

class STTTranscriber:
    """High-performance, completely offline speech transcriber."""

    def __init__(self, stt_config: Optional[STTConfig] = None) -> None:
        self.config = stt_config or config.stt
        logger.info(
            "Initializing Faster-Whisper model '%s' (Device=%s, Compute=%s)...",
            self.config.model_size,
            self.config.device,
            self.config.compute_type,
        )
        self.model = WhisperModel(
            model_size_or_path=self.config.model_size,
            device=self.config.device,
            compute_type=self.config.compute_type,
        )
        logger.info("Faster-Whisper model ready for local inference.")

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe 16-bit 16kHz PCM audio into text.

        :param audio_data: 1D numpy array of int16 samples.
        :return: Transcribed text string.
        """
        if len(audio_data) == 0:
            return ""

        # Normalize 16-bit PCM integer samples [-32768, 32767] to float32 [-1.0, 1.0]
        audio_float = audio_data.astype(np.float32) / 32768.0

        # Auto-detect language if set to 'auto'
        lang = None if self.config.language.lower() in ("auto", "none", "") else self.config.language

        # Context prompt primes Whisper for accurate Hindi/English voice commands
        prompt = "User speaking conversational Hindi and English commands: gaana chalao, open chrome, weather batao."

        segments, info = self.model.transcribe(
            audio_float,
            beam_size=5,
            best_of=5,
            initial_prompt=prompt,
            language=lang,
            vad_filter=False,  # AudioRecorder has already handled voice activity detection
        )

        self.last_detected_language = info.language
        logger.info("Transcribed audio (Detected language: %s, Probability: %.2f)", info.language, info.language_probability)

        full_text = " ".join(segment.text.strip() for segment in segments)
        return full_text.strip()
