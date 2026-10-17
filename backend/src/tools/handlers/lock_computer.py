"""Tool for locking the Windows workstation screen."""

from typing import Any
from src.automation.handlers.system_handler import SystemHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "lock_computer",
        "description": "Lock the Windows desktop computer or screen.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def execute() -> ExecutionResult:
    """Lock the Windows workstation."""
    return SystemHandler.control("lock")
