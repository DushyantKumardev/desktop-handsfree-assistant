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

        segments, info = self.model.transcribe(
            audio_float,
            beam_size=1,
            language=self.config.language,
            vad_filter=False,  # AudioRecorder has already handled voice activity detection
        )

        full_text = " ".join(segment.text.strip() for segment in segments)
        return full_text.strip()
