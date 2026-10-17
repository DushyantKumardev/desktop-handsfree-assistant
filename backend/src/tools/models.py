"""Tool calling data models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Represents a tool requested by the LLM."""
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """The clean response from the LLM."""
    spoken_reply: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_query: str = ""
    needs_followup: bool = False
