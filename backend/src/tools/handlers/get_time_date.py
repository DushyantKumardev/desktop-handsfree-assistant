"""Tool for retrieving current local time, date, or day of the week."""

from typing import Any
from src.automation.handlers.time_handler import TimeHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_time_date",
        "description": "Get current system time, today's date, or day of the week.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def execute() -> ExecutionResult:
    """Retrieve current time and date."""
    return TimeHandler.get_time()
