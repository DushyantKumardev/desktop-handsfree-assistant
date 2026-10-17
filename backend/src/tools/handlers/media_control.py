"""Tool for controlling currently playing background media on Windows."""

from typing import Any
from src.automation.handlers.system_handler import SystemHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "media_control",
        "description": "Control currently playing audio/video on Windows (pause, resume, skip to next, go to previous).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["play_pause", "next_track", "previous_track"],
                    "description": "'play_pause' to pause or resume playback, 'next_track' for next song, 'previous_track' for previous",
                }
            },
            "required": ["command"],
        },
    },
}


def execute(command: str = "play_pause") -> ExecutionResult:
    """Send Windows media key for playback control."""
    return SystemHandler.control(command)
