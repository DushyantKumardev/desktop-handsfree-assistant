"""Desktop OS Action Executor - executes collected tool calls via ToolRegistry."""

import logging
from src.tools.models import ToolCall
from src.automation.models import ExecutionResult

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes tool calls directly against the native ToolRegistry."""

    def execute_tool(self, tool_call: ToolCall) -> ExecutionResult:
        """Executes a single ToolCall using the ToolRegistry."""
        from src.tools.registry import ToolRegistry
        logger.info("Executing tool: '%s' with args: %s", tool_call.name, tool_call.args)
        return ToolRegistry.execute(tool_call.name, tool_call.args)

    def execute_tools(self, tool_calls: list[ToolCall]) -> list[ExecutionResult]:
        """Executes a list of collected ToolCalls in order."""
        return [self.execute_tool(tc) for tc in tool_calls]
