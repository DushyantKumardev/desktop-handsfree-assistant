"""Central configuration manager for Desktop Handsfree Assistant backend."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv
from src.core.constants import (
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_SAMPLE_RATE,
    DEFAULT_APP_ENV,
    DEFAULT_DEBUG,
    DEFAULT_WAKEWORD_MODELS,
    DEFAULT_WAKEWORD_THRESHOLD,
    DEFAULT_VAD_ENERGY_THRESHOLD,
    DEFAULT_VAD_SILENCE_TIMEOUT,
    DEFAULT_VAD_INITIAL_TIMEOUT,
    DEFAULT_VAD_MAX_RECORD_TIME,
    DEFAULT_STT_MODEL_SIZE,
    DEFAULT_STT_DEVICE,
    DEFAULT_STT_COMPUTE_TYPE,
    DEFAULT_STT_LANGUAGE,
)

# Automatically load environment variables from project-level .env if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# Silence benign Windows symlink warning from huggingface_hub
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

@dataclass(frozen=True)
class AudioConfig:
    """Hardware audio capture and streaming configuration."""
    sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", str(AUDIO_SAMPLE_RATE)))
    channels: int = int(os.getenv("AUDIO_CHANNELS", str(AUDIO_CHANNELS)))
    chunk_size: int = int(os.getenv("AUDIO_CHUNK_SIZE", str(AUDIO_CHUNK_SIZE)))
    device_index: Optional[int] = (
        int(os.getenv("AUDIO_INPUT_DEVICE_INDEX"))
        if os.getenv("AUDIO_INPUT_DEVICE_INDEX")
        else None
    )

@dataclass(frozen=True)
class WakeWordConfig:
    """Wake word model and detection threshold configuration."""
    models: List[str] = field(
        default_factory=lambda: (
            [m.strip() for m in os.getenv("WAKEWORD_MODELS").split(",") if m.strip()]
            if os.getenv("WAKEWORD_MODELS")
            else list(DEFAULT_WAKEWORD_MODELS)
        )
    )
    threshold: float = float(os.getenv("WAKEWORD_THRESHOLD", str(DEFAULT_WAKEWORD_THRESHOLD)))

@dataclass(frozen=True)
class VADConfig:
    """Voice Activity Detection and speech recording configuration."""
    energy_threshold: float = float(os.getenv("VAD_ENERGY_THRESHOLD", str(DEFAULT_VAD_ENERGY_THRESHOLD)))
    silence_timeout: float = float(os.getenv("VAD_SILENCE_TIMEOUT", str(DEFAULT_VAD_SILENCE_TIMEOUT)))
    initial_timeout: float = float(os.getenv("VAD_INITIAL_TIMEOUT", str(DEFAULT_VAD_INITIAL_TIMEOUT)))
    max_record_time: float = float(os.getenv("VAD_MAX_RECORD_TIME", str(DEFAULT_VAD_MAX_RECORD_TIME)))

@dataclass(frozen=True)
class STTConfig:
    """Local Speech-to-Text configuration using Faster-Whisper."""
    model_size: str = os.getenv("STT_MODEL_SIZE", DEFAULT_STT_MODEL_SIZE)
    device: str = os.getenv("STT_DEVICE", DEFAULT_STT_DEVICE)
    compute_type: str = os.getenv("STT_COMPUTE_TYPE", DEFAULT_STT_COMPUTE_TYPE)
    language: str = os.getenv("STT_LANGUAGE", DEFAULT_STT_LANGUAGE)

@dataclass(frozen=True)
class AppConfig:
    """Global backend application settings."""
    app_env: str = os.getenv("APP_ENV", DEFAULT_APP_ENV)
    debug: bool = os.getenv("DEBUG", str(DEFAULT_DEBUG)).lower() in ("true", "1", "yes")
    audio: AudioConfig = field(default_factory=AudioConfig)
    wakeword: WakeWordConfig = field(default_factory=WakeWordConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    stt: STTConfig = field(default_factory=STTConfig)

# Default global configuration instance
config = AppConfig()
