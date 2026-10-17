"""Tool for setting system master volume to an exact percentage."""

from typing import Any
from src.automation.handlers.system_handler import SystemHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "set_volume",
        "description": "Set Windows system master audio volume to an exact percentage (0 to 100).",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Volume percentage level from 0 to 100",
                }
            },
            "required": ["level"],
        },
    },
}


def execute(level: int) -> ExecutionResult:
    """Set master volume percent."""
    return SystemHandler.control(f"volume_set:{level}")
