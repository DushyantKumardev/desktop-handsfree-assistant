"""Desktop OS Automation module for executing actions on Windows."""

from .models import ExecutionResult
from .executor import ActionExecutor

__all__ = ["ActionExecutor", "ExecutionResult"]
