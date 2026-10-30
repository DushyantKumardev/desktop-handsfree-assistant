"""Action and Reminder Scheduler: manages timers, delayed system actions, and context tracking."""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.server.ws_server import ws_server

logger = logging.getLogger("scheduler")


@dataclass
class ScheduledTask:
    """Represents a scheduled timer, reminder, or delayed system action."""

    id: str
    description: str
    trigger_time: float
    action_type: str  # "reminder" or "system_action"
    target_tool: Optional[str] = None
    target_args: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    _timer: Optional[threading.Timer] = field(default=None, repr=False)

    @property
    def remaining_seconds(self) -> float:
        """Returns the number of seconds remaining until trigger."""
        return max(0.0, self.trigger_time - time.time())

    def format_remaining(self) -> str:
        """Human readable remaining time (e.g. '4m 30s', '45s', '1h 12m')."""
        secs = int(self.remaining_seconds)
        if secs < 60:
            return f"{secs}s"
        mins = secs // 60
        rem_secs = secs % 60
        if mins < 60:
            return f"{mins}m {rem_secs}s" if rem_secs > 0 else f"{mins}m"
        hours = mins // 60
        rem_mins = mins % 60
        return f"{hours}h {rem_mins}m"


class ActionScheduler:
    """Thread-safe scheduler for timers, reminders, and delayed tool executions."""

    def __init__(self) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._counter = 1

    def schedule(
        self,
        delay_seconds: float,
        description: str,
        action_type: str = "reminder",
        target_tool: Optional[str] = None,
        target_args: Optional[Dict[str, Any]] = None,
    ) -> ScheduledTask:
        """Schedules a new action or reminder after delay_seconds."""
        with self._lock:
            task_id = str(self._counter)
            self._counter += 1

            trigger_time = time.time() + max(1.0, float(delay_seconds))
            task = ScheduledTask(
                id=task_id,
                description=description.strip(),
                trigger_time=trigger_time,
                action_type=action_type,
                target_tool=target_tool,
                target_args=target_args or {},
            )

            # Start Python background timer thread
            timer = threading.Timer(max(1.0, float(delay_seconds)), self._on_task_triggered, args=[task_id])
            timer.daemon = True
            task._timer = timer
            self._tasks[task_id] = task
            timer.start()

            logger.info(
                "Task #%s scheduled: '%s' in %.1fs (%s)",
                task_id,
                description,
                delay_seconds,
                action_type,
            )
            return task

    def cancel(self, identifier: str) -> Optional[ScheduledTask]:
        """Cancels a scheduled task by ID or keyword matching description."""
        clean_id = identifier.lower().strip().lstrip("#")
        with self._lock:
            # 1. Exact ID match
            if clean_id in self._tasks:
                task = self._tasks.pop(clean_id)
                if task._timer:
                    task._timer.cancel()
                logger.info("Task #%s ('%s') cancelled.", task.id, task.description)
                return task

            # 2. Match by description substring
            for tid, t in list(self._tasks.items()):
                if clean_id in t.description.lower():
                    task = self._tasks.pop(tid)
                    if task._timer:
                        task._timer.cancel()
                    logger.info("Task #%s ('%s') cancelled via keyword match.", task.id, task.description)
                    return task

        return None

    def get_active_tasks(self) -> List[ScheduledTask]:
        """Returns all currently active, non-expired tasks."""
        with self._lock:
            now = time.time()
            active = [t for t in self._tasks.values() if t.trigger_time > now]
            return sorted(active, key=lambda x: x.trigger_time)

    def get_context_summary(self) -> str:
        """
        Produces a concise context line for the LLM system prompt.
        Example: 'None' or 'ID #1: tea break (due in 2m 10s); ID #2: lock computer (due in 15m)'
        """
        active = self.get_active_tasks()
        if not active:
            return "No active schedules."

        items = [f"ID #{t.id}: '{t.description}' (in {t.format_remaining()})" for t in active]
        return "; ".join(items)

    def _on_task_triggered(self, task_id: str) -> None:
        """Internal callback executed when a scheduled timer expires."""
        task: Optional[ScheduledTask] = None
        with self._lock:
            task = self._tasks.pop(task_id, None)

        if not task:
            return

        logger.info("Scheduled task #%s triggered: '%s' (%s)", task.id, task.description, task.action_type)

        # 1. Broadcast native desktop notification to frontend
        notification_title = "Timer & Reminder Alert ⏱️" if task.action_type == "reminder" else "Scheduled Action ⚙️"
        notification_body = task.description or "Your scheduled task has triggered."
        ws_server.broadcast_notification(notification_title, notification_body, task_id=task.id)

        # 2. Execute target tool if system_action
        if task.action_type == "system_action" and task.target_tool:
            try:
                from src.tools.registry import ToolRegistry
                logger.info("Executing scheduled tool: %s with %s", task.target_tool, task.target_args)
                ToolRegistry.execute(task.target_tool, task.target_args or {})
            except Exception as e:
                logger.error("Failed to execute scheduled tool %s: %s", task.target_tool, e)

        # 3. Spoken alert via TTS if speech engine is available
        try:
            from src.tts.synthesizer import TTSSynthesizer
            synth = TTSSynthesizer.get_instance()
            if synth:
                spoken_text = f"Reminder: {task.description}." if task.action_type == "reminder" else f"Scheduled action completed: {task.description}."
                # Speak in background thread so it doesn't block the scheduler
                threading.Thread(target=synth.speak, args=[spoken_text], kwargs={"stream": True}, daemon=True).start()
        except Exception as err:
            logger.debug("TTS announcement for schedule failed: %s", err)


# Global singleton instance
action_scheduler = ActionScheduler()
