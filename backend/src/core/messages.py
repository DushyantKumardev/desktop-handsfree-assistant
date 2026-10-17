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

    NO_SPEECH_HEARD: Final[str] = "I could not hear anything."
    EMPTY_QUERY: Final[str] = "I did not catch that."
    DEFAULT_GREETING: Final[str] = "Hello! How can I assist you?"
    DEFAULT_FALLBACK: Final[str] = "Right away."
    ACTION_COMPLETED: Final[str] = "Action completed."
    TOOL_DEFAULT_WORKING: Final[str] = "Working on that for you, give me a moment."


# ---------------------------------------------------------------------------
# Conversational Tool Engagement Phrases (Spoken before tool execution)
# ---------------------------------------------------------------------------
class ToolEngagementPhrases:
    """Phrases spoken to engage the user before running long operations."""

    WEB_SEARCH_HINDI: Final[list[str]] = [
        "Main abhi internet par check karke batata hoon, ek second.",
        "Dekhta hoon, online search kar raha hoon, ek pal dijiye.",
        "Iske baare mein abhi search karta hoon, bas ek second.",
    ]

    WEB_SEARCH_ENGLISH_QUERY: Final[list[str]] = [
        "Let me check the web for {query}, give me just a moment.",
        "Looking that up on the web for you right now, one second.",
        "Searching online for {query}, give me a second.",
        "Let me find that information for you, one moment.",
    ]

    WEB_SEARCH_ENGLISH_DEFAULT: Final[list[str]] = [
        "Let me check the web for that, give me just a moment.",
        "Looking into that right now, one moment.",
        "Searching online for you, give me a second.",
    ]

    PLAY_MEDIA_HINDI_QUERY: Final[str] = "YouTube par {query} dhoondh raha hoon, ek second."
    PLAY_MEDIA_HINDI_DEFAULT: Final[str] = "YouTube chala raha hoon, ek second."
    PLAY_MEDIA_ENGLISH_QUERY: Final[str] = "Looking up {query} on YouTube for you, one moment."
    PLAY_MEDIA_ENGLISH_DEFAULT: Final[str] = "Opening YouTube for you, one moment."

    OPEN_APP_HINDI: Final[str] = "{app} open kar raha hoon, ek second."
    OPEN_APP_ENGLISH: Final[str] = "Opening {app} for you right away."


# ---------------------------------------------------------------------------
# Default Spoken Phrases When LLM is Silent
# ---------------------------------------------------------------------------
class ToolDefaultPhrases:
    """Spoken phrases used as fallbacks when LLM emits a tool call without speech."""

    OPEN_APP: Final[str] = "Opening {app}."
    PLAY_MEDIA: Final[str] = "Playing {query} on YouTube."
    PLAY_MEDIA_DEFAULT: Final[str] = "Opening YouTube."
    MEDIA_CONTROL_NEXT: Final[str] = "Skipping track."
    MEDIA_CONTROL_TOGGLE: Final[str] = "Toggling playback."
    SET_VOLUME: Final[str] = "Setting volume to {level} percent."
    ADJUST_VOLUME: Final[str] = "Turning volume {direction}."
    MUTE_VOLUME: Final[str] = "Toggling mute."
    LOCK_COMPUTER: Final[str] = "Locking your computer."
    WEB_SEARCH: Final[str] = "Searching for {query}."
    WEB_SEARCH_DEFAULT: Final[str] = "Searching the web."


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
