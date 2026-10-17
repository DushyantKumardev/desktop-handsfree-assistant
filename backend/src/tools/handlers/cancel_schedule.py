"""Tool for cancelling scheduled timers, reminders, and delayed actions."""

from typing import Any
from src.automation.models import ExecutionResult
from src.automation.scheduler import action_scheduler
from src.core.messages import ActionMessages

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "cancel_schedule",
        "description": "Cancel an active timer, scheduled reminder, or delayed action by ID or keyword. Call this when the user says 'cancel my timer', 'stop the reminder', 'cancel timer for tea', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Task ID (e.g. '1', '2') or description keyword (e.g. 'tea', 'timer', 'lock').",
                }
            },
            "required": ["identifier"],
        },
    },
}


def execute(identifier: str) -> ExecutionResult:
    """Cancel the matching scheduled task."""
    task = action_scheduler.cancel(identifier)
    if task:
        msg = ActionMessages.SCHEDULE_CANCELLED.format(description=task.description)
        spoken = f"Cancelled schedule for {task.description}."
        return ExecutionResult(
            success=True,
            action="cancel_schedule",
            message=msg,
            spoken_override=spoken,
        )

    msg = ActionMessages.SCHEDULE_NOT_FOUND.format(identifier=identifier)
    spoken = f"Could not find any active schedule matching {identifier}."
    return ExecutionResult(
        success=False,
        action="cancel_schedule",
        message=msg,
        spoken_override=spoken,
    )
