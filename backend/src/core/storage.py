"""Persistent local storage for user preferences and runtime state."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SETTINGS_FILE = STORAGE_DIR / "user_settings.json"


class SettingsStorage:
    """Thread-safe persistent settings storage with in-memory caching."""

    _CACHE: dict[str, Any] = {}
    _INITIALIZED = False

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._INITIALIZED:
            return
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    cls._CACHE = json.load(f)
            except Exception as e:
                logger.error("Failed to load settings file, initializing empty: %s", e)
                cls._CACHE = {}
        else:
            cls._CACHE = {}
        cls._INITIALIZED = True

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a setting from memory cache (loading from disk if needed)."""
        cls._ensure_loaded()
        return cls._CACHE.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Save a setting to cache and write to disk."""
        cls._ensure_loaded()
        cls._CACHE[key] = value
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._CACHE, f, indent=2)
        except Exception as e:
            logger.error("Failed to persist setting '%s': %s", key, e)

    @classmethod
    def get_speaking_speed(cls, default: float = 1.15) -> float:
        """Get saved speaking speed from storage/cache."""
        val = cls.get("speaking_speed", default)
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @classmethod
    def set_speaking_speed(cls, speed: float) -> None:
        """Save speaking speed to storage/cache."""
        cls.set("speaking_speed", round(float(speed), 2))
