"""System clock and date inquiry handler."""

import datetime
from src.automation.models import ExecutionResult


class TimeHandler:
    """Handles fetching current local system time, day, and date."""

    @staticmethod
    def get_time() -> ExecutionResult:
        """Returns and formats the current local time and date."""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        day_str = now.strftime("%A, %B %d")
        spoken = f"The time is {time_str} on {day_str}."

        return ExecutionResult(
            success=True,
            action="get_time",
            message=f"Current time: {time_str}, {day_str}",
            spoken_override=spoken,
        )
