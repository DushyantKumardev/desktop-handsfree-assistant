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
    """Retrieve all currently active schedules and return structured data to the LLM."""
    active_tasks = action_scheduler.get_active_tasks()
    if not active_tasks:
        summary = "No active timers or scheduled reminders."
    elif len(active_tasks) == 1:
        t = active_tasks[0]
        summary = f"1 active timer: '{t.description}' with {t.format_remaining()} remaining."
    else:
        items = [f"'{t.description}' with {t.format_remaining()} remaining" for t in active_tasks]
        summary = f"{len(active_tasks)} active timers: {', '.join(items)}."

    return ExecutionResult(
        success=True,
        action="get_schedules",
        message=summary,
        spoken_override=None,
        data={"summary": summary, "task_count": len(active_tasks)},
    )
