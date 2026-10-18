"""Central constants for application messages, responses, errors, and phrases.

This file provides a unified location for all conversational responses,
spoken interaction phrases, action execution feedback, and error messages.
"""

from typing import Final


# ---------------------------------------------------------------------------
# Error Messages
# ---------------------------------------------------------------------------
class ErrorMessages:
    """Error messages returned or logged across the assistant pipeline."""

    LLM_INFERENCE_ERROR: Final[str] = "I encountered an error reaching the assistant brain."
    TTS_NOT_INITIALIZED: Final[str] = "TTS Synthesizer is not initialized."
    UNKNOWN_TOOL: Final[str] = "Unknown tool '{tool_name}'."
    INVALID_TOOL_ARGS: Final[str] = "Invalid arguments for {tool_name}: {error}"
    TOOL_EXECUTION_ERROR: Final[str] = "Error executing {tool_name}: {error}"
    APP_NO_NAME: Final[str] = "No application name specified."
    APP_LAUNCH_FAILED: Final[str] = "Failed to launch {target}: {error}"
    SYSTEM_CONTROL_UNKNOWN: Final[str] = "Unknown system control target: {command}"
    SYSTEM_CONTROL_FAILED: Final[str] = "System control failed: {error}"
    BROWSER_OPEN_FAILED: Final[str] = "Could not open browser: {error}"
    SPEED_PARSE_ERROR: Final[str] = "Could not parse '{speed}', reset to normal."


# ---------------------------------------------------------------------------
# Assistant Conversational Responses
# ---------------------------------------------------------------------------
class AssistantResponses:
    """Core spoken conversational feedback phrases."""

    NO_SPEECH_HEARD: Final[str] = "Didn't catch that."
    EMPTY_QUERY: Final[str] = "Missed that, say again?"
    DEFAULT_GREETING: Final[str] = "Yo, what's up?"
    DEFAULT_FALLBACK: Final[str] = "On it."
    ACTION_COMPLETED: Final[str] = "Done."
    TOOL_DEFAULT_WORKING: Final[str] = "On it, one sec."


# ---------------------------------------------------------------------------
# Conversational Tool Engagement Phrases (Spoken before tool execution)
# ---------------------------------------------------------------------------
class ToolEngagementPhrases:
    """Phrases spoken to engage the user before running long operations."""

    WEB_SEARCH_HINDI: Final[list[str]] = [
        "Ek sec ruk, check karta hoon.",
        "Ruk, online check karta hoon.",
        "Dekhta hoon, bas ek sec.",
    ]

    WEB_SEARCH_ENGLISH_QUERY: Final[list[str]] = [
        "Let me check that real quick.",
        "Looking into that, one sec.",
        "On it, checking the web.",
        "Let me check.",
    ]

    WEB_SEARCH_ENGLISH_DEFAULT: Final[list[str]] = [
        "Let me check.",
        "Looking into it, one sec.",
        "Checking the web now.",
    ]

    PLAY_MEDIA_HINDI_QUERY: Final[str] = "YouTube par chala raha hoon, ek sec."
    PLAY_MEDIA_HINDI_DEFAULT: Final[str] = "YouTube khol raha hoon."
    PLAY_MEDIA_ENGLISH_QUERY: Final[str] = "Playing {query}."
    PLAY_MEDIA_ENGLISH_DEFAULT: Final[str] = "Opening YouTube."

    OPEN_APP_HINDI: Final[str] = "{app} khol raha hoon."
    OPEN_APP_ENGLISH: Final[str] = "Opening {app}."


# ---------------------------------------------------------------------------
# Default Spoken Phrases When LLM is Silent
# ---------------------------------------------------------------------------
class ToolDefaultPhrases:
    """Spoken phrases used as fallbacks when LLM emits a tool call without speech."""

    OPEN_APP: Final[str] = "Opening {app}."
    PLAY_MEDIA: Final[str] = "Playing {query}."
    PLAY_MEDIA_DEFAULT: Final[str] = "Opening YouTube."
    MEDIA_CONTROL_NEXT: Final[str] = "Skipped."
    MEDIA_CONTROL_TOGGLE: Final[str] = "Done."
    SET_VOLUME: Final[str] = "Volume at {level}%."
    ADJUST_VOLUME: Final[str] = "Volume {direction}."
    MUTE_VOLUME: Final[str] = "Muted."
    LOCK_COMPUTER: Final[str] = "Locking screen."
    WEB_SEARCH: Final[str] = "Checking {query}."
    WEB_SEARCH_DEFAULT: Final[str] = "Let me check."
    SCHEDULE_ACTION: Final[str] = "Ya got it, timer set."
    CANCEL_SCHEDULE: Final[str] = "Cancelled."


# ---------------------------------------------------------------------------
# Action Execution Status Messages
# ---------------------------------------------------------------------------
class ActionMessages:
    """Status messages returned inside ExecutionResult objects."""

    APP_LAUNCHED: Final[str] = "Successfully launched {target}."

    VOLUME_SET: Final[str] = "Master volume set to {percent}%."
    VOLUME_INCREASED: Final[str] = "Volume increased."
    VOLUME_DECREASED: Final[str] = "Volume decreased."
    VOLUME_MUTED: Final[str] = "Volume mute toggled."

    TRACK_NEXT: Final[str] = "Skipped to next track."
    TRACK_PREV: Final[str] = "Returned to previous track."
    PLAYBACK_TOGGLED: Final[str] = "Media playback toggled."
    COMPUTER_LOCKED: Final[str] = "Computer locked."

    TIME_REPORT: Final[str] = "Current time: {time_str}, {day_str}"
    TIME_SPOKEN: Final[str] = "The time is {time_str} on {day_str}."

    WEB_SEARCH_RETRIEVED: Final[str] = "Retrieved web search results for '{query}'."
    GOOGLE_SEARCH_OPENED: Final[str] = "Opened Google search for '{query}'."
    YOUTUBE_OPENED: Final[str] = "Opened YouTube in browser."
    YOUTUBE_SEARCH_OPENED: Final[str] = "Opened YouTube search for '{query}'."

    SCHEDULE_CREATED: Final[str] = "Scheduled '{description}' in {time_formatted}."
    SCHEDULE_CANCELLED: Final[str] = "Cancelled schedule for '{description}'."
    SCHEDULE_NOT_FOUND: Final[str] = "No active schedule found matching '{identifier}'."


# ---------------------------------------------------------------------------
# Speaking Speed Responses & Messages
# ---------------------------------------------------------------------------
class SpeakingSpeedMessages:
    """Responses and messages for TTS speaking speed adjustments."""

    FASTER_SPOKEN: Final[str] = "I am speaking faster now at {speed:.2f}x speed. How is this pace?"
    FASTER_MSG: Final[str] = "Increased speaking speed to {speed:.2f}x."

    SLOWER_SPOKEN: Final[str] = "I am speaking slower now at {speed:.2f}x speed. Is this better?"
    SLOWER_MSG: Final[str] = "Decreased speaking speed to {speed:.2f}x."

    FAST_SPOKEN: Final[str] = "I am speaking fast now. Let me know if you need any adjustments."
    FAST_MSG: Final[str] = "Set speaking speed to fast ({speed:.2f}x)."

    VERY_FAST_SPOKEN: Final[str] = "I am speaking very fast now."
    VERY_FAST_MSG: Final[str] = "Set speaking speed to very fast ({speed:.2f}x)."

    SLOW_SPOKEN: Final[str] = "I will speak slowly now. Is this pace comfortable?"
    SLOW_MSG: Final[str] = "Set speaking speed to slow ({speed:.2f}x)."

    VERY_SLOW_SPOKEN: Final[str] = "I am speaking very slowly now."
    VERY_SLOW_MSG: Final[str] = "Set speaking speed to very slow ({speed:.2f}x)."

    NORMAL_SPOKEN: Final[str] = "Speaking speed is back to normal."
    NORMAL_MSG: Final[str] = "Reset speaking speed to normal ({speed:.2f}x)."

    CUSTOM_SPOKEN: Final[str] = "Speaking speed set to {speed:.2f}x."
    CUSTOM_MSG: Final[str] = "Set speaking speed to {speed:.2f}x."

    RESET_FALLBACK_SPOKEN: Final[str] = "Speaking speed reset to normal."
