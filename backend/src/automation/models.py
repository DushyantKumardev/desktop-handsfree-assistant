"""Data models for desktop OS automation execution."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """Result returned after attempting to execute an intent."""
    success: bool
    action: str
    message: str
    spoken_override: Optional[str] = None
