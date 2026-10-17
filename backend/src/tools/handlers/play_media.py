"""Tool for searching and playing songs, artists, or videos on YouTube."""

from typing import Any
from src.automation.handlers.web_handler import WebHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "play_media",
        "description": "Search and play a song, artist, playlist, or video on YouTube. Call this whenever the user says 'play X', 'open youtube and search/play X', or 'find X on youtube'.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The song, artist, or video to play on YouTube, e.g. 'arijit singh', 'lo-fi hip hop', 'diljit dosanjh'",
                }
            },
            "required": ["query"],
        },
    },
}


def execute(query: str) -> ExecutionResult:
    """Search and launch playback on YouTube."""
    return WebHandler.search(f"play {query}")
