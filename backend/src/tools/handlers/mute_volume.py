"""Tool for toggling system master audio mute."""

from typing import Any
from src.automation.handlers.system_handler import SystemHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "mute_volume",
        "description": "Toggle system master audio mute or unmute.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def execute() -> ExecutionResult:
    """Toggle audio mute."""
    return SystemHandler.control("mute")
