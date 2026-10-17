"""LLM Brain: The central intelligence of the desktop voice assistant."""

import json
import logging
import re
from typing import Any, Callable, Optional
from openai import OpenAI
from src.core.config import LLMConfig, config
from src.tools import DESKTOP_TOOLS, ToolCall, LLMResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the voice brain of a desktop computer. You control the OS with tools.

Always speak a short natural sentence FIRST before any tool call. Never stay silent.
Examples: "Ahh got it, one sec.", "Looking that up for you.", "Opening that now.", "Checking the time."

Then call the right tool:
- search / who is / what is / latest news → web_search
- play / open youtube and play → play_media
- open chrome / notepad / youtube → open_app
- time / date → get_time_date
- volume / mute / pause / next → set_volume / mute_volume / media_control
- speak faster / slower / speed up / slow down / normal speed → set_speaking_speed

Pure chat or greetings → just reply naturally in 1-3 sentences. No tools.

Everything you say goes straight to TTS. Speak only clean plain sentences. No markdown, no asterisks, no bullets, no emojis, no symbols.

Support English, Hindi and Hinglish naturally.
"""


class LLMBrain:
    """The Assistant's LLM Brain: streams spoken conversational replies and collects native tool calls."""

    def __init__(self, llm_config: Optional[LLMConfig] = None) -> None:
        self.config = llm_config or config.llm
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=10.0,
        )
        logger.info(
            "LLMBrain initialized with tools: %s (Model: %s)",
            self.config.base_url,
            self.config.model,
        )

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
        - Collects any requested ToolCalls and returns LLMResponse(spoken_reply, tool_calls).
        """
        if not user_query.strip():
            return LLMResponse(spoken_reply="I did not catch that.", tool_calls=[], raw_query="")

        # Ensure max_tokens has at least 450 tokens to prevent cutting off multi-sentence answers
        effective_max_tokens = max(self.config.max_tokens, 450)

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ],
            "tools": DESKTOP_TOOLS,
            "tool_choice": "auto",
            "temperature": self.config.temperature,
            "max_tokens": effective_max_tokens,
            "stream": True,
        }

        # Extra body for OpenRouter to suppress reasoning delays
        if "openrouter" in self.config.base_url.lower():
            extra_body: dict[str, Any] = {
                "reasoning": {"max_tokens": 0},
                "thinking": {"type": "disabled"},
            }
            if self.config.reasoning_effort:
                extra_body["reasoning_effort"] = self.config.reasoning_effort
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
                                sentence = match.group(1).strip()
                                buf_text = match.group(2).lstrip()
                                if callable(on_sentence_ready):
                                    on_sentence_ready(sentence)
                                if not first_sentence_emitted:
                                    first_sentence_emitted = True
                                    if callable(on_reply_ready):
                                        on_reply_ready(sentence)
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
            remaining_sentence = "".join(sentence_buffer).strip()
            if remaining_sentence:
                if callable(on_sentence_ready):
                    on_sentence_ready(remaining_sentence)
                if not first_sentence_emitted:
                    first_sentence_emitted = True
                    if callable(on_reply_ready):
                        on_reply_ready(remaining_sentence)

            full_speech = "".join(content_tokens).strip()

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

            # If LLM called tools without speaking connecting text, provide default phrase
            if collected_tools and not full_speech:
                first_tool = collected_tools[0]
                full_speech = self._generate_default_phrase(first_tool.name, first_tool.args)
                if full_speech:
                    if callable(on_sentence_ready):
                        on_sentence_ready(full_speech)
                    if not first_sentence_emitted and callable(on_reply_ready):
                        on_reply_ready(full_speech)

            return LLMResponse(
                spoken_reply=full_speech or "Hello! How can I assist you?",
                tool_calls=collected_tools,
                raw_query=user_query,
            )

        except Exception as e:
            logger.error("LLM inference failed: %s", e, exc_info=True)
            fallback_text = "I encountered an error reaching the assistant brain."
            if callable(on_reply_ready):
                on_reply_ready(fallback_text)
            return LLMResponse(
                spoken_reply=fallback_text,
                tool_calls=[],
                raw_query=user_query,
            )

    @staticmethod
    def _generate_default_phrase(tool_name: str, args: dict[str, Any]) -> str:
        """Fallback phrase if model was silent when requesting a tool."""
        if tool_name == "open_app":
            return f"Opening {args.get('app_name', 'application')}."
        elif tool_name == "play_media":
            q = args.get("query", "")
            return f"Playing {q} on YouTube." if q else "Opening YouTube."
        elif tool_name == "media_control":
            return "Skipping track." if args.get("command") == "next_track" else "Toggling playback."
        elif tool_name == "set_volume":
            return f"Setting volume to {args.get('level', 50)} percent."
        elif tool_name == "adjust_volume":
            return f"Turning volume {args.get('direction', 'up')}."
        elif tool_name == "mute_volume":
            return "Toggling mute."
        elif tool_name == "get_time_date":
            return "Checking the time."
        elif tool_name == "lock_computer":
            return "Locking your computer."
        elif tool_name == "web_search":
            q = args.get("query", "")
            return f"Searching for {q}." if q else "Searching the web."
        elif tool_name == "set_speaking_speed":
            # Let the tool's spoken override speak at the new speed directly
            return ""
        return "Right away."
