"""Tool for checking active timers, reminders, and scheduled tasks."""

from typing import Any
from src.automation.models import ExecutionResult
from src.automation.scheduler import action_scheduler

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_schedules",
        "description": "Check currently active timers, reminders, and scheduled actions. Call this whenever the user asks 'how much time is left on my timer?', 'what timers are running?', 'check my timer status', or 'what is scheduled?'.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}


def execute() -> ExecutionResult:
    """Retrieve and report all currently active schedules."""
    active_summary = action_scheduler.get_context_summary()
    active_tasks = action_scheduler.get_active_tasks()

    if not active_tasks:
        spoken = "You have no active timers or scheduled reminders."
    elif len(active_tasks) == 1:
        t = active_tasks[0]
        spoken = f"Your {t.description} has {t.format_remaining()} remaining."
    else:
        items = [f"{t.description} with {t.format_remaining()} left" for t in active_tasks]
        spoken = f"You have {len(active_tasks)} active schedules: {', '.join(items)}."

    return ExecutionResult(
        success=True,
        action="get_schedules",
        message=active_summary,
        spoken_override=spoken,
    )
