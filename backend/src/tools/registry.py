"""Tool Registry that aggregates self-contained tool definitions and handlers."""

import logging
from typing import Any, Callable
from src.core.messages import ErrorMessages
from src.automation.models import ExecutionResult
from .handlers import ALL_TOOL_MODULES

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry that collects definitions and executes tool handlers directly."""

    _DEFINITIONS: list[dict[str, Any]] = []
    _HANDLERS: dict[str, Callable[..., ExecutionResult]] = {}

    @classmethod
    def _initialize(cls) -> None:
        if cls._DEFINITIONS and cls._HANDLERS:
            return
        cls._DEFINITIONS = []
        cls._HANDLERS = {}
        for mod in ALL_TOOL_MODULES:
            tool_def = getattr(mod, "DEFINITION", None)
            tool_fn = getattr(mod, "execute", None)
            if tool_def and tool_fn:
                cls._DEFINITIONS.append(tool_def)
                name = tool_def["function"]["name"]
                cls._HANDLERS[name] = tool_fn

    @classmethod
    def get_definitions(cls) -> list[dict[str, Any]]:
        """Returns the list of OpenAI-format tool definitions."""
        cls._initialize()
        return cls._DEFINITIONS

    @classmethod
    def execute(cls, tool_name: str, args: dict[str, Any]) -> ExecutionResult:
        """Executes the tool handler matching tool_name directly with args."""
        cls._initialize()
        handler = cls._HANDLERS.get(tool_name)
        if not handler:
            logger.warning("Unregistered tool requested: '%s'", tool_name)
            return ExecutionResult(
                success=False,
                action=tool_name,
                message=ErrorMessages.UNKNOWN_TOOL.format(tool_name=tool_name),
            )

        logger.info("Executing tool '%s' with args: %s", tool_name, args)
        try:
            return handler(**args)
        except TypeError as te:
            logger.error("Argument error for tool '%s': %s", tool_name, te)
            return ExecutionResult(
                success=False,
                action=tool_name,
                message=ErrorMessages.INVALID_TOOL_ARGS.format(tool_name=tool_name, error=te),
            )
        except Exception as e:
            logger.error("Failed to execute tool '%s': %s", tool_name, e)
            return ExecutionResult(
                success=False,
                action=tool_name,
                message=ErrorMessages.TOOL_EXECUTION_ERROR.format(tool_name=tool_name, error=e),
            )
