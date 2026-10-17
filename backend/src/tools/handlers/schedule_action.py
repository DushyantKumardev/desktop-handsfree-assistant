"""Tool for scheduling timers, reminders, and delayed system actions."""

from typing import Any, Dict, Optional
from src.automation.models import ExecutionResult
from src.automation.scheduler import action_scheduler
from src.core.messages import ActionMessages

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "schedule_action",
        "description": "Schedule a delayed timer, reminder, or future system action. Call this whenever the user says 'set a timer for X', 'remind me in X to Y', 'lock computer in X minutes', or 'mute in X seconds'.",
        "parameters": {
            "type": "object",
            "properties": {
                "delay_seconds": {
                    "type": "number",
                    "description": "Delay in seconds from now (e.g. 60 for 1 min, 300 for 5 min, 1800 for 30 min, 3600 for 1 hour).",
                },
                "description": {
                    "type": "string",
                    "description": "Description of the reminder or task, e.g. 'tea break', '5 minute timer', 'lock computer'.",
                },
                "action_type": {
                    "type": "string",
                    "enum": ["reminder", "system_action"],
                    "description": "'reminder' for spoken alarm/alert, 'system_action' to trigger a system tool when time is reached.",
                },
                "target_tool": {
                    "type": "string",
                    "description": "Optional name of tool to execute when action_type is 'system_action' (e.g. 'lock_computer', 'mute_volume', 'set_volume').",
                },
                "target_args": {
                    "type": "object",
                    "description": "Optional dictionary of arguments to pass to target_tool.",
                },
            },
            "required": ["delay_seconds", "description"],
        },
    },
}


def execute(
    delay_seconds: float,
    description: str,
    action_type: str = "reminder",
    target_tool: Optional[str] = None,
    target_args: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    """Schedule the requested timer, reminder, or delayed action."""
    task = action_scheduler.schedule(
        delay_seconds=delay_seconds,
        description=description,
        action_type=action_type,
        target_tool=target_tool,
        target_args=target_args,
    )

    remaining_str = task.format_remaining()
    msg = ActionMessages.SCHEDULE_CREATED.format(description=task.description, time_formatted=remaining_str)
    spoken = f"Timer set for {task.description} in {remaining_str}." if action_type == "reminder" else f"Scheduled {task.description} in {remaining_str}."

    return ExecutionResult(
        success=True,
        action="schedule_action",
        message=msg,
        spoken_override=spoken,
    )
