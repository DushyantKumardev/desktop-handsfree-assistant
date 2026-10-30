"""Voice Activity Detection (VAD) audio recorder for user speech commands."""

import logging
import time
from typing import Callable, List, Optional
import numpy as np
from src.core.config import VADConfig, config
from src.audio.capture import AudioCapture

logger = logging.getLogger(__name__)

class AudioRecorder:
    """
    Records an utterance from AudioCapture using Voice Activity Detection (VAD).
    Starts recording when speech is detected and stops when silence follows.
    """

    def __init__(self, vad_config: Optional[VADConfig] = None) -> None:
        self.config = vad_config or config.vad
        self._cancelled = False

    def cancel(self) -> None:
        """Immediately interrupts any ongoing recording session."""
        self._cancelled = True

    @staticmethod
    def calculate_energy(chunk: np.ndarray) -> float:
        """Calculate Root Mean Square (RMS) energy of an audio chunk."""
        if len(chunk) == 0:
            return 0.0
        # Convert to float to avoid 16-bit integer overflow during squaring
        samples = chunk.astype(np.float32)
        return float(np.sqrt(np.mean(samples ** 2)))

    def record_phrase(
        self,
        audio_capture: AudioCapture,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_chunk: Optional[Callable[[float], None]] = None,
    ) -> np.ndarray:
        """
        Record a speech command synchronously until silence is detected.

        :param audio_capture: Active AudioCapture stream instance.
        :param on_speech_start: Optional callback when voice activity first begins.
        :param on_speech_chunk: Optional callback for each recorded chunk with current energy.
        :return: 1D numpy array of 16-bit PCM audio containing the complete user utterance.
        """
        # 1. Flush any stale audio chunks (like the wake word 'Alexa') before recording
        audio_capture.flush_queue()
        self._cancelled = False

        recorded_chunks: List[np.ndarray] = []
        has_started_speaking = False
        silence_duration = 0.0

        # Duration of each chunk in seconds (e.g. 1280 / 16000 = 0.08s = 80ms)
        chunk_seconds = audio_capture.config.chunk_size / audio_capture.config.sample_rate

        logger.info(
            "AudioRecorder listening for speech (Threshold=%.1f, SilenceTimeout=%.1fs, InitialTimeout=%.1fs)...",
            self.config.energy_threshold,
            self.config.silence_timeout,
            self.config.initial_timeout,
        )

        start_time = time.time()

        while True:
            if self._cancelled:
                logger.info("Audio recording aborted by cancellation.")
                return np.array([], dtype=np.int16)

            elapsed = time.time() - start_time

            # 2. Safety maximum duration check
            if elapsed > self.config.max_record_time:
                logger.info("Maximum recording duration reached (%.1fs). Ending record.", self.config.max_record_time)
                break

            # 3. Timeout if user took too long to begin speaking after wake word
            if not has_started_speaking and elapsed > self.config.initial_timeout:
                logger.info("Initial speech timeout (%.1fs). User did not speak.", self.config.initial_timeout)
                break

            chunk = audio_capture.read_chunk(timeout=0.2)
            if chunk is None:
                continue

            energy = self.calculate_energy(chunk)
            is_speech = energy >= self.config.energy_threshold

            if is_speech:
                if not has_started_speaking:
                    has_started_speaking = True
                    logger.info("User speech started! (Energy=%.1f)", energy)
                    if on_speech_start:
                        on_speech_start()

                # User is talking: reset silence duration
                silence_duration = 0.0
                recorded_chunks.append(chunk)

                if on_speech_chunk:
                    on_speech_chunk(energy)

            elif has_started_speaking:
                # User was talking, but this chunk is silent
                silence_duration += chunk_seconds
                recorded_chunks.append(chunk)

                if silence_duration >= self.config.silence_timeout:
                    logger.info("Silence detected (%.2fs). User finished speaking.", silence_duration)
                    break
            else:
                # Waiting for user to start speaking:
                # Keep rolling buffer of 2 chunks (~160ms) to preserve the onset of the first syllable
                if len(recorded_chunks) >= 2:
                    recorded_chunks.pop(0)
                recorded_chunks.append(chunk)

        if not recorded_chunks:
            return np.array([], dtype=np.int16)

        return np.concatenate(recorded_chunks)
