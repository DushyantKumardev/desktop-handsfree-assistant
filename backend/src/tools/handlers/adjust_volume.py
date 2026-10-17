"""Tool for increasing or decreasing system master volume."""

from typing import Any
from src.automation.handlers.system_handler import SystemHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "adjust_volume",
        "description": "Increase or decrease Windows audio volume by a step.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "'up' to increase volume, 'down' to decrease volume",
                }
            },
            "required": ["direction"],
        },
    },
}


def execute(direction: str = "up") -> ExecutionResult:
    """Step volume up or down."""
    return SystemHandler.control(f"volume_{direction}")
