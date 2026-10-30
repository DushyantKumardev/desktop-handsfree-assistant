"""Local neural Text-to-Speech (TTS) synthesizer using Piper and sounddevice."""

import io
import logging
import re
import time
import urllib.request
import wave
from pathlib import Path
from typing import Optional
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
from piper.config import SynthesisConfig
from src.core.config import TTSConfig, config
from src.core.storage import SettingsStorage

logger = logging.getLogger(__name__)

class TTSSynthesizer:
    """High-quality offline neural voice synthesizer."""

    VOICE_URLS = {
        "en_US-lessac-medium": {
            "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
            "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        },
        "hi_IN-rohan-medium": {
            "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx",
            "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx.json",
        },
        "hi_IN-priyamvada-medium": {
            "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx",
            "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx.json",
        },
    }

    _INSTANCE: Optional["TTSSynthesizer"] = None

    def __init__(self, tts_config: Optional[TTSConfig] = None) -> None:
        self.config = tts_config or config.tts
        self._stop_requested = False
        # Restore speed from persistent storage cache, falling back to config default
        self.speed = SettingsStorage.get_speaking_speed(default=float(self.config.speed))
        self.models_dir = Path(__file__).resolve().parent.parent.parent / "models" / "piper"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_voices: dict[str, PiperVoice] = {}
        TTSSynthesizer._INSTANCE = self

        # Pre-load default voice
        self._get_voice(self.config.voice)

    def stop(self) -> None:
        """Immediately halts any active speech synthesis and audio playback."""
        self._stop_requested = True
        try:
            sd.stop()
        except Exception:
            pass

    def reset(self) -> None:
        """Resets the stop flag so new speech synthesis can proceed."""
        self._stop_requested = False

    @classmethod
    def get_instance(cls) -> Optional["TTSSynthesizer"]:
        """Returns the active TTS synthesizer instance."""
        return cls._INSTANCE

    def set_speed(self, speed: float) -> float:
        """Sets speaking speed multiplier (0.5 to 2.5) and persists to storage cache."""
        self.speed = max(0.5, min(2.5, round(float(speed), 2)))
        SettingsStorage.set_speaking_speed(self.speed)
        logger.info("TTS speaking speed updated and saved to storage: %.2fx", self.speed)
        return self.speed

    def adjust_speed(self, delta: float) -> float:
        """Adjusts current speaking speed by delta (e.g. +0.2 or -0.2) and persists to storage."""
        return self.set_speed(self.speed + delta)

    @staticmethod
    def clean_spoken_text(text: str) -> str:
        """Strips markdown asterisks, hashtags, and formatting characters before speaking."""
        if not text:
            return ""
        # Remove markdown bold/italic asterisks & underscores (**bold** -> bold)
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
        cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)
        cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)
        cleaned = re.sub(r"#{1,6}\s*", "", cleaned)  # Headers
        cleaned = re.sub(r"`[^`]*`", "", cleaned)     # Code blocks
        cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)  # Links
        cleaned = re.sub(r"<[^>]+>", "", cleaned)     # Strip XML/HTML tags like <followup/>
        cleaned = re.sub(r"[\*#~`>]", "", cleaned)
        # Normalize non-breaking and narrow unicode spaces (e.g. \u202f, \u00a0)
        cleaned = re.sub(r"[\u00a0\u202f\u200b]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect language based on Unicode script. Returns 'hi' for Hindi Devanagari, 'en' otherwise."""
        if any("\u0900" <= char <= "\u097f" for char in text):
            return "hi"
        return "en"

    def _get_voice(self, voice_name: str) -> PiperVoice:
        """Retrieve cached PiperVoice or load it from disk."""
        if voice_name not in self._loaded_voices:
            model_path, config_path = self._ensure_model(voice_name)
            logger.info("Loading Piper neural voice: %s", voice_name)
            self._loaded_voices[voice_name] = PiperVoice.load(str(model_path), config_path=str(config_path))
        return self._loaded_voices[voice_name]

    def _ensure_model(self, voice_name: str) -> tuple[Path, Path]:
        """Verify model files exist locally or download from Hugging Face."""
        model_path = self.models_dir / f"{voice_name}.onnx"
        config_path = self.models_dir / f"{voice_name}.onnx.json"

        if model_path.exists() and config_path.exists():
            return model_path, config_path

        urls = self.VOICE_URLS.get(voice_name)
        if not urls:
            raise ValueError(f"Unknown voice: '{voice_name}'. Pre-configured voices: {list(self.VOICE_URLS.keys())}")

        print(f"[+] Downloading Piper neural voice '{voice_name}' (~50MB)...")
        urllib.request.urlretrieve(urls["config"], config_path)
        urllib.request.urlretrieve(urls["model"], model_path)
        print("[+] Voice download complete.")

        return model_path, config_path

    def synthesize(self, text: str, voice_name: Optional[str] = None) -> tuple[np.ndarray, int]:
        """
        Synthesize text into a 16-bit PCM numpy audio array with automatic voice routing.
        """
        clean_text = self.clean_spoken_text(text)
        if not clean_text:
            return np.array([], dtype=np.int16), 22050

        # Auto-detect language if voice not explicitly provided
        if not voice_name:
            lang = self.detect_language(clean_text)
            voice_name = "hi_IN-priyamvada-medium" if lang == "hi" else self.config.voice

        voice = self._get_voice(voice_name)

        # length_scale inversely controls speaking pace (e.g. 1.15 speed = ~0.87 scale)
        speed = max(0.5, min(2.5, self.speed))
        syn_config = SynthesisConfig(length_scale=1.0 / speed)

        # Piper yields AudioChunk objects with audio_int16_array
        audio_chunks = [
            chunk.audio_int16_array
            for chunk in voice.synthesize(clean_text, syn_config=syn_config)
        ]
        if not audio_chunks:
            return np.array([], dtype=np.int16), 22050

        audio_array = np.concatenate(audio_chunks)
        sample_rate = voice.config.sample_rate

        # Add 400ms trailing silence padding so the soundcard doesn't cut off the last word
        trailing_padding = np.zeros(int(sample_rate * 0.4), dtype=np.int16)
        audio_array = np.concatenate([audio_array, trailing_padding])

        return audio_array, sample_rate

    def synthesize_stream(self, text: str, voice_name: Optional[str] = None):
        """
        Yield (chunk_pcm_array, sample_rate) dynamically as Piper synthesizes audio.
        Allows instant playback before the full sentence is synthesized.
        """
        clean_text = self.clean_spoken_text(text)
        if not clean_text:
            return

        if not voice_name:
            lang = self.detect_language(clean_text)
            voice_name = "hi_IN-priyamvada-medium" if lang == "hi" else self.config.voice

        voice = self._get_voice(voice_name)
        speed = max(0.5, min(2.5, self.speed))
        syn_config = SynthesisConfig(length_scale=1.0 / speed)
        sample_rate = voice.config.sample_rate

        for chunk in voice.synthesize(clean_text, syn_config=syn_config):
            if chunk.audio_int16_array is not None and len(chunk.audio_int16_array) > 0:
                yield chunk.audio_int16_array, sample_rate

    def stream_speak(self, text: str, voice_name: Optional[str] = None) -> None:
        """
        Synthesize and play audio in real time via sounddevice.OutputStream.
        Playback starts on the very first audio chunk (~50-100ms).
        """
        clean_text = self.clean_spoken_text(text)
        if not clean_text or self._stop_requested:
            return

        if not voice_name:
            lang = self.detect_language(clean_text)
            voice_name = "hi_IN-priyamvada-medium" if lang == "hi" else self.config.voice

        voice = self._get_voice(voice_name)
        sample_rate = voice.config.sample_rate

        speed = max(0.5, min(2.5, self.speed))
        syn_config = SynthesisConfig(length_scale=1.0 / speed)

        # Open low-latency output stream
        with sd.OutputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
            for chunk in voice.synthesize(clean_text, syn_config=syn_config):
                if self._stop_requested:
                    stream.abort()
                    return
                if chunk.audio_int16_array is not None and len(chunk.audio_int16_array) > 0:
                    stream.write(chunk.audio_int16_array)

            if self._stop_requested:
                stream.abort()
                return

            # Trailing silence padding so Windows audio driver doesn't clip the final phoneme
            trailing_padding = np.zeros(int(sample_rate * 0.3), dtype=np.int16)
            stream.write(trailing_padding)

    def speak(self, text: str, voice_name: Optional[str] = None, stream: bool = True) -> None:
        """
        Synthesize text and play through sounddevice.
        If stream=True (default), streams chunks directly to the soundcard for minimum latency.
        """
        if self._stop_requested:
            return

        if stream:
            self.stream_speak(text, voice_name=voice_name)
            return

        audio_array, sample_rate = self.synthesize(text, voice_name=voice_name)
        if len(audio_array) == 0 or self._stop_requested:
            return

        sd.play(audio_array, samplerate=sample_rate)
        while sd.get_stream() and sd.get_stream().active:
            if self._stop_requested:
                sd.stop()
                break
            time.sleep(0.04)

