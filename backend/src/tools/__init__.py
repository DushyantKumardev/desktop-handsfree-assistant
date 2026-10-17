"""Desktop Assistant native tools package."""

from .models import ToolCall, LLMResponse
from .registry import ToolRegistry

DESKTOP_TOOLS = ToolRegistry.get_definitions()

__all__ = ["DESKTOP_TOOLS", "ToolCall", "LLMResponse", "ToolRegistry"]
