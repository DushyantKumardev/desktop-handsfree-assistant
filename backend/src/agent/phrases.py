"""Conversational tool reaction phrases and delay speech formatters."""

import random
from typing import Any, Dict


def format_delay_phrase(seconds: float) -> str:
    """Formats numeric seconds into human speech (e.g. '5 minutes', '45 seconds')."""
    s = int(seconds)
    if s >= 3600:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h} hour{'s' if h > 1 else ''}" + (f" {m} minute{'s' if m > 1 else ''}" if m else "")
    elif s >= 60:
        m = s // 60
        sec = s % 60
        return f"{m} minute{'s' if m > 1 else ''}" + (f" {sec} second{'s' if sec > 1 else ''}" if sec else "")
    return f"{s} second{'s' if s > 1 else ''}"


def generate_tool_phrase(tool_name: str, args: Dict[str, Any]) -> str:
    """Returns a natural Siri/Google-style crisp phrase when the LLM calls a tool without conversational speech."""
    if tool_name == "schedule_action":
        delay = args.get("delay_seconds", 0)
        dur = format_delay_phrase(delay) if delay else "that"
        return random.choice([
            f"Ya got it, {dur} on the clock.",
            f"On it, {dur} sec.",
            f"Say less, {dur} starting now.",
            f"Bet, {dur}.",
        ])
    elif tool_name == "cancel_schedule":
        return random.choice([
            "Cancelled.",
            "Done, killed that timer.",
            "Got it, cancelled.",
        ])
    elif tool_name == "open_app":
        app = args.get("app_name", "app")
        return random.choice([
            f"Opening {app}.",
            f"On it, launching {app}.",
            f"Say less, opening {app}.",
        ])
    elif tool_name == "play_media":
        q = args.get("query", "")
        return random.choice([
            f"Playing {q}." if q else "Opening YouTube.",
            f"On it, playing {q}." if q else "On it, opening YouTube.",
            f"Say less, pulling up {q}." if q else "Say less, opening YouTube.",
        ])
    elif tool_name == "media_control":
        cmd = args.get("command", "")
        return "Skipped." if cmd == "next_track" else "Done."
    elif tool_name == "set_volume":
        lvl = args.get("level", 50)
        return random.choice([
            f"Volume at {lvl}%.",
            f"Set to {lvl}%.",
        ])
    elif tool_name == "adjust_volume":
        d = args.get("direction", "up")
        return f"Volume {d}."
    elif tool_name == "mute_volume":
        return random.choice(["Muted.", "Done, muted."])
    elif tool_name == "lock_computer":
        return random.choice(["Locking down.", "Screen locked."])
    elif tool_name == "web_search":
        q = args.get("query", "")
        return random.choice([
            "Let me check.",
            f"Checking {q}." if q else "Checking the web.",
            "On it, looking that up.",
        ])
    elif tool_name in ("set_speaking_speed", "get_schedules"):
        return ""
    return random.choice(["On it.", "Done.", "Ya got it.", "Say less."])
