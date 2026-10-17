"""Structured Intent models for desktop assistant actions."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class IntentResult:
    """Represents the parsed intent and action to execute."""
    action: str  # "open_app", "web_search", "get_time", "system_volume", "conversation"
    target: Optional[str] = None  # target app name, url, query, etc.
    speech_reply: str = ""  # Natural 1-sentence reply to speak via TTS
    raw_query: str = ""  # The original transcribed user speech
