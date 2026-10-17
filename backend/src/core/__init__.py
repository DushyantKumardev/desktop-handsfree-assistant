"""Core package for shared configurations, logging, constants, and utilities."""

from .messages import (
    ErrorMessages,
    AssistantResponses,
    ToolEngagementPhrases,
    ToolDefaultPhrases,
    ActionMessages,
    SpeakingSpeedMessages,
)

from .constants import DEFAULT_SYSTEM_PROMPT

__all__ = [
    "ErrorMessages",
    "AssistantResponses",
    "ToolEngagementPhrases",
    "ToolDefaultPhrases",
    "ActionMessages",
    "SpeakingSpeedMessages",
    "DEFAULT_SYSTEM_PROMPT",
]
