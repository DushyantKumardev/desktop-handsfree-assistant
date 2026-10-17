"""Tool for dynamically controlling TTS voice speaking speed."""

from typing import Any, Union
from src.core.messages import ErrorMessages, SpeakingSpeedMessages
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
            message=ErrorMessages.TTS_NOT_INITIALIZED,
        )

    str_speed = str(speed).strip().lower()

    if str_speed in ("faster", "speed up", "tez", "aur tez", "more fast"):
        new_speed = synth.adjust_speed(0.25)
        override = SpeakingSpeedMessages.FASTER_SPOKEN.format(speed=new_speed)
        msg = SpeakingSpeedMessages.FASTER_MSG.format(speed=new_speed)

    elif str_speed in ("slower", "slow down", "dheere", "aur dheere", "aram se"):
        new_speed = synth.adjust_speed(-0.25)
        override = SpeakingSpeedMessages.SLOWER_SPOKEN.format(speed=new_speed)
        msg = SpeakingSpeedMessages.SLOWER_MSG.format(speed=new_speed)

    elif str_speed in ("fast", "tezi se"):
        new_speed = synth.set_speed(1.4)
        override = SpeakingSpeedMessages.FAST_SPOKEN
        msg = SpeakingSpeedMessages.FAST_MSG.format(speed=new_speed)

    elif str_speed in ("very_fast", "very fast", "bahut tez"):
        new_speed = synth.set_speed(1.7)
        override = SpeakingSpeedMessages.VERY_FAST_SPOKEN
        msg = SpeakingSpeedMessages.VERY_FAST_MSG.format(speed=new_speed)

    elif str_speed in ("slow", "dheere bolo", "dheere"):
        new_speed = synth.set_speed(0.85)
        override = SpeakingSpeedMessages.SLOW_SPOKEN
        msg = SpeakingSpeedMessages.SLOW_MSG.format(speed=new_speed)

    elif str_speed in ("very_slow", "very slow", "bahut dheere"):
        new_speed = synth.set_speed(0.7)
        override = SpeakingSpeedMessages.VERY_SLOW_SPOKEN
        msg = SpeakingSpeedMessages.VERY_SLOW_MSG.format(speed=new_speed)

    elif str_speed in ("normal", "default", "standard", "reset"):
        new_speed = synth.set_speed(1.15)
        override = SpeakingSpeedMessages.NORMAL_SPOKEN
        msg = SpeakingSpeedMessages.NORMAL_MSG.format(speed=new_speed)

    else:
        # Try parsing numeric speed like "1.3"
        try:
            num = float(str_speed)
            new_speed = synth.set_speed(num)
            override = SpeakingSpeedMessages.CUSTOM_SPOKEN.format(speed=new_speed)
            msg = SpeakingSpeedMessages.CUSTOM_MSG.format(speed=new_speed)
        except ValueError:
            new_speed = synth.set_speed(1.15)
            override = SpeakingSpeedMessages.RESET_FALLBACK_SPOKEN
            msg = ErrorMessages.SPEED_PARSE_ERROR.format(speed=speed)

    return ExecutionResult(
        success=True,
        action="set_speaking_speed",
        message=msg,
        spoken_override=override,
    )
