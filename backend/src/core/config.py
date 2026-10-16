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
)

# Automatically load environment variables from project-level .env if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

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
class AppConfig:
    """Global backend application settings."""
    app_env: str = os.getenv("APP_ENV", DEFAULT_APP_ENV)
    debug: bool = os.getenv("DEBUG", str(DEFAULT_DEBUG)).lower() in ("true", "1", "yes")
    audio: AudioConfig = field(default_factory=AudioConfig)
    wakeword: WakeWordConfig = field(default_factory=WakeWordConfig)

# Default global configuration instance
config = AppConfig()
