"""Microphone audio streaming and hardware abstraction using sounddevice."""

import logging
import queue
from typing import Callable, List, Optional
import numpy as np
import sounddevice as sd
from src.core.config import AudioConfig, config

logger = logging.getLogger(__name__)

class AudioCapture:
    """Manages real-time microphone stream input with subscriber dispatching."""

    def __init__(self, audio_config: Optional[AudioConfig] = None) -> None:
        self.config = audio_config or config.audio
        self._stream: Optional[sd.InputStream] = None
        self._subscribers: List[Callable[[np.ndarray], None]] = []
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=100)
        self._is_active = False

    @staticmethod
    def list_input_devices() -> List[dict]:
        """Enumerate all available physical audio input devices."""
        devices = sd.query_devices()
        input_devices = []
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                input_devices.append({
                    "index": idx,
                    "name": dev.get("name"),
                    "channels": dev.get("max_input_channels"),
                    "sample_rate": dev.get("default_samplerate"),
                })
        return input_devices

    def add_subscriber(self, callback: Callable[[np.ndarray], None]) -> None:
        """Register a callback that receives raw 1D int16 audio frames in real time."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def remove_subscriber(self, callback: Callable[[np.ndarray], None]) -> None:
        """Unregister an audio frame subscriber."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Internal callback invoked by sounddevice for each new buffer from the soundcard."""
        if status:
            logger.warning("Audio input warning status: %s", status)

        # 1D array of 16-bit PCM samples
        chunk = indata[:, 0].copy()

        # Send to internal queue
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            # Drop oldest frame if consumer lags
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(chunk)
            except (queue.Empty, queue.Full):
                pass

        # Dispatch to registered subscribers
        for subscriber in self._subscribers:
            try:
                subscriber(chunk)
            except Exception as e:
                logger.error("Error in audio subscriber callback: %s", e)

    def start(self) -> None:
        """Open the microphone stream and begin capturing."""
        if self._is_active:
            return

        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype="int16",
            blocksize=self.config.chunk_size,
            device=self.config.device_index,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._is_active = True
        logger.info(
            "AudioCapture stream started (SampleRate=%dHz, ChunkSize=%d, Device=%s)",
            self.config.sample_rate,
            self.config.chunk_size,
            self.config.device_index if self.config.device_index is not None else "Default",
        )

    def read_chunk(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        """Synchronously pull the next captured audio chunk from the queue."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def flush_queue(self) -> None:
        """Discard all pending audio chunks in the internal queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def stop(self) -> None:
        """Close and release the microphone input stream."""
        if not self._is_active:
            return

        self._is_active = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.error("Error while closing audio input stream: %s", e)
            self._stream = None
        logger.info("AudioCapture stream stopped.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
