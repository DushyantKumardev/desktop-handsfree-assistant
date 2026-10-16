"""Wake word detection engine powered by openWakeWord."""

import logging
from typing import Callable, Dict, List, Optional
import numpy as np
import openwakeword
from openwakeword.model import Model
from openwakeword.utils import download_models
from src.core.config import WakeWordConfig, config
from src.audio.capture import AudioCapture

logger = logging.getLogger(__name__)

class WakeWordDetector:
    """Detects specified wake words from audio streams using local ONNX models."""

    def __init__(
        self,
        wakeword_config: Optional[WakeWordConfig] = None,
        on_detection: Optional[Callable[[str, float], None]] = None,
    ) -> None:
        self.config = wakeword_config or config.wakeword
        self.on_detection = on_detection
        self._audio_capture: Optional[AudioCapture] = None

        logger.info("Initializing WakeWordDetector for models: %s", self.config.models)

        # Load the ONNX model directly (bundled models like alexa exist offline)
        try:
            self.model = Model(
                wakeword_models=self.config.models,
                inference_framework="onnx",
            )
        except Exception as err:
            logger.info("Direct model load failed (%s), attempting download...", err)
            try:
                download_models(model_names=self.config.models)
            except Exception as dl_err:
                logger.warning("Download check failed: %s", dl_err)
            self.model = Model(
                wakeword_models=self.config.models,
                inference_framework="onnx",
            )
        logger.info("WakeWordDetector models loaded successfully.")

    def process_chunk(self, chunk: np.ndarray) -> Dict[str, float]:
        """
        Process a single 16-bit 16kHz audio frame and check for wake word activations.

        :param chunk: 1D numpy array of int16 audio samples (typically 1280 samples).
        :return: Dict of model predictions {model_name: confidence_score}.
        """
        predictions: Dict[str, float] = self.model.predict(chunk)

        for model_name, score in predictions.items():
            if score >= self.config.threshold:
                logger.info(
                    "Wake word detected! Model='%s', Confidence=%.3f (Threshold=%.2f)",
                    model_name,
                    score,
                    self.config.threshold,
                )
                if self.on_detection:
                    try:
                        self.on_detection(model_name, float(score))
                    except Exception as e:
                        logger.error("Error executing wake word detection callback: %s", e)

        return predictions

    def start_listening(self, audio_capture: AudioCapture) -> None:
        """Attach to an active AudioCapture stream as an audio subscriber."""
        self._audio_capture = audio_capture
        self._audio_capture.add_subscriber(self.process_chunk)
        logger.info("WakeWordDetector attached to AudioCapture stream.")

    def stop_listening(self) -> None:
        """Detach from the AudioCapture stream."""
        if self._audio_capture is not None:
            self._audio_capture.remove_subscriber(self.process_chunk)
            self._audio_capture = None
            logger.info("WakeWordDetector detached from AudioCapture stream.")

    def reset(self) -> None:
        """Reset internal model state/buffers."""
        self.model.reset()
