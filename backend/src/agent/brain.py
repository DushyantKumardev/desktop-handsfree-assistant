import datetime
import json
import logging
import random
import re
from typing import Any, Callable, Optional
from openai import OpenAI
from src.core.config import LLMConfig, config
from src.core.constants import DEFAULT_SYSTEM_PROMPT
from src.core.messages import AssistantResponses, ErrorMessages, ToolDefaultPhrases
from src.tools import DESKTOP_TOOLS, ToolCall, LLMResponse
from src.automation.scheduler import action_scheduler

logger = logging.getLogger(__name__)

FOLLOWUP_TAG_REGEX = re.compile(r"<\s*follow_?up(?:\s*\/|\s*>.*?<\/\s*follow_?up\s*|\s*\/?>)", re.IGNORECASE)


class LLMBrain:
    """The Assistant's LLM Brain: streams spoken conversational replies and collects native tool calls."""

    def __init__(self, llm_config: Optional[LLMConfig] = None) -> None:
        self.config = llm_config or config.llm
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=10.0,
        )
        self.conversation_history: list[dict[str, str]] = []
        logger.info(
            "LLMBrain initialized with tools: %s (Model: %s)",
            self.config.base_url,
            self.config.model,
        )

    def reset_conversation(self) -> None:
        """Clears recent conversation history."""
        self.conversation_history.clear()

    def process_command(
        self,
        user_query: str,
        on_sentence_ready: Optional[Callable[[str], None]] = None,
        on_reply_ready: Optional[Callable[[str], None]] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> LLMResponse:
        """
        Processes user query with the LLM.
        - Streams spoken sentences dynamically via on_sentence_ready as they complete.
        - Detects <followup/> XML tag to automatically trigger listening cycle.
        - Collects any requested ToolCalls and returns LLMResponse.
        """
        if not user_query.strip():
            return LLMResponse(spoken_reply=AssistantResponses.EMPTY_QUERY, tool_calls=[], raw_query="", needs_followup=False)

        # Inject real-time system clock and active schedules directly into system prompt
        now_str = datetime.datetime.now().strftime("%I:%M %p, %A, %B %d, %Y").lstrip("0")
        schedules_str = action_scheduler.get_context_summary()
        prompt_content = DEFAULT_SYSTEM_PROMPT.format(current_time=now_str, active_schedules=schedules_str)

        # Build message payload with conversation memory
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt_content},
        ]
        # Include last 4 conversational turns (2 pairs) for fast context with minimal tokens
        messages.extend(self.conversation_history[-4:])
        messages.append({"role": "user", "content": user_query})

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "tools": DESKTOP_TOOLS,
            "tool_choice": "auto",
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }

        # Extra body to suppress reasoning delays across providers
        extra_body: dict[str, Any] = {}
        base_url_lower = self.config.base_url.lower()

        if "openrouter" in base_url_lower:
            extra_body.update({
                "reasoning": {"max_tokens": 0},
                "thinking": {"type": "disabled"},
            })
            if self.config.reasoning_effort:
                extra_body["reasoning_effort"] = self.config.reasoning_effort
        elif "ollama" in base_url_lower or "11434" in base_url_lower:
            extra_body.update({
                "think": False,
                "reasoning_effort": "none",
            })

        if extra_body:
            request_kwargs["extra_body"] = extra_body

        try:
            stream = self.client.chat.completions.create(**request_kwargs)

            content_tokens: list[str] = []
            sentence_buffer: list[str] = []
            tool_calls_dict: dict[int, dict[str, Any]] = {}
            first_sentence_emitted = False

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 1. Stream spoken text
                if delta.content:
                    content_tokens.append(delta.content)
                    sentence_buffer.append(delta.content)
                    if callable(on_token):
                        on_token(delta.content)

                    # Check for sentence boundary (period, exclamation, question mark followed by space or newline)
                    buf_text = "".join(sentence_buffer)
                    if any(p in delta.content for p in (".", "!", "?", "\n")):
                        while True:
                            match = re.search(r"^([\s\S]*?[.!?\n])(\s+[\s\S]*|$)", buf_text)
                            if match and match.group(1).strip():
                                raw_sentence = match.group(1).strip()
                                buf_text = match.group(2).lstrip()
                                # Clean XML tags and followup tags so they are not sent to TTS or UI chunk
                                clean_sentence = FOLLOWUP_TAG_REGEX.sub("", raw_sentence)
                                clean_sentence = re.sub(r"<[^>]+>", "", clean_sentence).strip()
                                if clean_sentence:
                                    if callable(on_sentence_ready):
                                        on_sentence_ready(clean_sentence)
                                    if not first_sentence_emitted:
                                        first_sentence_emitted = True
                                        if callable(on_reply_ready):
                                            on_reply_ready(clean_sentence)
                            else:
                                break
                        sentence_buffer = [buf_text] if buf_text else []

                # 2. Accumulate tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {
                                "name": tc.function.name or "" if tc.function else "",
                                "arguments": tc.function.arguments or "" if tc.function else "",
                            }
                        else:
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_dict[idx]["name"] += tc.function.name
                                if tc.function.arguments:
                                    tool_calls_dict[idx]["arguments"] += tc.function.arguments

            # Flush any remaining un-yielded sentence from buffer
            remaining_raw = "".join(sentence_buffer).strip()
            if remaining_raw:
                remaining_clean = FOLLOWUP_TAG_REGEX.sub("", remaining_raw)
                remaining_clean = re.sub(r"<[^>]+>", "", remaining_clean).strip()
                if remaining_clean:
                    if callable(on_sentence_ready):
                        on_sentence_ready(remaining_clean)
                    if not first_sentence_emitted:
                        first_sentence_emitted = True
                        if callable(on_reply_ready):
                            on_reply_ready(remaining_clean)

            raw_speech = "".join(content_tokens).strip()
            has_followup = bool(FOLLOWUP_TAG_REGEX.search(raw_speech))
            clean_speech = FOLLOWUP_TAG_REGEX.sub("", raw_speech)
            clean_speech = re.sub(r"<[^>]+>", "", clean_speech).strip()

            # 3. Collect tool calls
            collected_tools: list[ToolCall] = []
            for idx in sorted(tool_calls_dict.keys()):
                item = tool_calls_dict[idx]
                t_name = item["name"]
                t_args_str = item["arguments"]
                try:
                    t_args = json.loads(t_args_str) if t_args_str else {}
                except Exception:
                    t_args = {}
                collected_tools.append(ToolCall(name=t_name, args=t_args))

            # If LLM called tools without speaking connecting text, use natural Siri/Google style phrasing
            if collected_tools and not clean_speech:
                first_tool = collected_tools[0]
                clean_speech = self._generate_default_phrase(first_tool.name, first_tool.args)
                if clean_speech:
                    if callable(on_sentence_ready):
                        on_sentence_ready(clean_speech)
                    if not first_sentence_emitted and callable(on_reply_ready):
                        on_reply_ready(clean_speech)

            if not clean_speech and not collected_tools:
                q_lower = user_query.lower()
                if any(w in q_lower for w in ("timer", "schedule", "reminder", "alarm", "clock")):
                    active_tasks = action_scheduler.get_active_tasks()
                    if active_tasks:
                        t = active_tasks[0]
                        clean_speech = f"Ya got {t.format_remaining()} left on {t.description}."
                    else:
                        clean_speech = "No timers running right now."

            final_reply = clean_speech or AssistantResponses.DEFAULT_GREETING

            # Append to persistent conversational memory
            self.conversation_history.append({"role": "user", "content": user_query})
            self.conversation_history.append({"role": "assistant", "content": final_reply})
            if len(self.conversation_history) > 12:
                self.conversation_history = self.conversation_history[-12:]

            return LLMResponse(
                spoken_reply=final_reply,
                tool_calls=collected_tools,
                raw_query=user_query,
                needs_followup=has_followup,
            )

        except Exception as e:
            logger.error("LLM inference failed: %s", e, exc_info=True)
            fallback_text = ErrorMessages.LLM_INFERENCE_ERROR
            if callable(on_reply_ready):
                on_reply_ready(fallback_text)
            return LLMResponse(
                spoken_reply=fallback_text,
                tool_calls=[],
                raw_query=user_query,
            )

    @staticmethod
    def _format_delay(seconds: float) -> str:
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

    @classmethod
    def _generate_default_phrase(cls, tool_name: str, args: dict[str, Any]) -> str:
        """Human-like short, catchy conversational phrase with zero API cost."""
        if tool_name == "schedule_action":
            delay = args.get("delay_seconds", 0)
            dur = cls._format_delay(delay) if delay else "that"
            return random.choice([
                f"Ya got it, {dur} on the clock.",
                f"On it, {dur} set.",
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
