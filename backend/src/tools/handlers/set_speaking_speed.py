"""Tool for dynamically controlling TTS voice speaking speed."""

from typing import Any, Union
from src.automation.models import ExecutionResult
from src.tts.synthesizer import TTSSynthesizer

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "set_speaking_speed",
        "description": "Adjust how fast or slow the assistant speaks. Use this whenever the user asks to speak faster, slower, speed up, slow down, or set speaking speed to normal.",
        "parameters": {
            "type": "object",
            "properties": {
                "speed": {
                    "type": "string",
                    "description": "Desired speed: 'faster', 'slower', 'fast', 'slow', 'normal', 'very_fast', 'very_slow', or a numeric multiplier like '1.3'.",
                }
            },
            "required": ["speed"],
        },
    },
}


def execute(speed: Union[str, float, int] = "normal") -> ExecutionResult:
    """Adjust TTS speaking speed dynamically."""
    synth = TTSSynthesizer.get_instance()
    if not synth:
        return ExecutionResult(
            success=False,
            action="set_speaking_speed",
            message="TTS Synthesizer is not initialized.",
        )

    str_speed = str(speed).strip().lower()

    if str_speed in ("faster", "speed up", "tez", "aur tez", "more fast"):
        new_speed = synth.adjust_speed(0.25)
        override = f"I am speaking faster now at {new_speed:.2f}x speed. How is this pace?"
        msg = f"Increased speaking speed to {new_speed:.2f}x."

    elif str_speed in ("slower", "slow down", "dheere", "aur dheere", "aram se"):
        new_speed = synth.adjust_speed(-0.25)
        override = f"I am speaking slower now at {new_speed:.2f}x speed. Is this better?"
        msg = f"Decreased speaking speed to {new_speed:.2f}x."

    elif str_speed in ("fast", "tezi se"):
        new_speed = synth.set_speed(1.4)
        override = "I am speaking fast now. Let me know if you need any adjustments."
        msg = f"Set speaking speed to fast ({new_speed:.2f}x)."

    elif str_speed in ("very_fast", "very fast", "bahut tez"):
        new_speed = synth.set_speed(1.7)
        override = "I am speaking very fast now."
        msg = f"Set speaking speed to very fast ({new_speed:.2f}x)."

    elif str_speed in ("slow", "dheere bolo", "dheere"):
        new_speed = synth.set_speed(0.85)
        override = "I will speak slowly now. Is this pace comfortable?"
        msg = f"Set speaking speed to slow ({new_speed:.2f}x)."

    elif str_speed in ("very_slow", "very slow", "bahut dheere"):
        new_speed = synth.set_speed(0.7)
        override = "I am speaking very slowly now."
        msg = f"Set speaking speed to very slow ({new_speed:.2f}x)."

    elif str_speed in ("normal", "default", "standard", "reset"):
        new_speed = synth.set_speed(1.15)
        override = "Speaking speed is back to normal."
        msg = f"Reset speaking speed to normal ({new_speed:.2f}x)."

    else:
        # Try parsing numeric speed like "1.3"
        try:
            num = float(str_speed)
            new_speed = synth.set_speed(num)
            override = f"Speaking speed set to {new_speed:.2f}x."
            msg = f"Set speaking speed to {new_speed:.2f}x."
        except ValueError:
            new_speed = synth.set_speed(1.15)
            override = "Speaking speed reset to normal."
            msg = f"Could not parse '{speed}', reset to normal."

    return ExecutionResult(
        success=True,
        action="set_speaking_speed",
        message=msg,
        spoken_override=override,
    )
