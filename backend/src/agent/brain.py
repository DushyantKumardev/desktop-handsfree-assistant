"""LLM Brain: The central intelligence of the desktop voice assistant."""

import json
import logging
from typing import Any, Callable, Optional
from openai import OpenAI
from src.core.config import LLMConfig, config
from src.tools import DESKTOP_TOOLS, ToolCall, LLMResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the intelligent voice assistant brain of a desktop computer.
You have access to native tools to control the operating system.

RULES FOR USING TOOLS:
1. Always call the appropriate tool when the user asks you to perform an action:
   - "open youtube", "open chrome", "open notepad" -> Call open_app(app_name=...)
   - "open youtube and search/play X", "play X" -> Call play_media(query="X")
   - "search for X", "open chrome and search for X", "look up X" -> Call web_search(query="X")
   - "what time is it", "today's date" -> Call get_time_date()
   - "set volume to 40%", "mute", "pause music", "next song" -> Call set_volume / mute_volume / media_control
2. ALWAYS speak a short, friendly connecting sentence (1 brief sentence) to the user when executing any tool.
   Examples:
   - "Opening YouTube for you."
   - "Searching for Tesla new car."
   - "Playing Diljit Dosanjh on YouTube."
   - "Setting master volume to 40 percent."
   - "Checking the time."
3. ONLY if the user is saying hello, greeting, or having small talk (e.g. "who are you?", "hello"), respond directly without calling any tools.
4. Support English, Hindi, and Hinglish naturally.
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
        on_reply_ready: Optional[Callable[[str], None]] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> LLMResponse:
        """
        Processes user query with the LLM.
        - Streams the spoken sentence and emits on_reply_ready for TTS.
        - Collects any requested ToolCalls and returns LLMResponse(spoken_reply, tool_calls).
        """
        if not user_query.strip():
            return LLMResponse(spoken_reply="I did not catch that.", tool_calls=[], raw_query="")

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ],
            "tools": DESKTOP_TOOLS,
            "tool_choice": "auto",
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
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
            tool_calls_dict: dict[int, dict[str, Any]] = {}
            reply_emitted = False

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 1. Stream spoken text
                if delta.content:
                    content_tokens.append(delta.content)
                    if callable(on_token):
                        on_token(delta.content)

                    # Trigger early TTS on first sentence boundary
                    if not reply_emitted and any(punct in delta.content for punct in (".", "!", "?", "\n")):
                        reply_emitted = True
                        early_text = "".join(content_tokens).strip()
                        if callable(on_reply_ready) and early_text:
                            on_reply_ready(early_text)

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

            # Emit reply for TTS if not already emitted
            if not reply_emitted and callable(on_reply_ready) and full_speech:
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
            return f"Playing {args.get('query', '')} on YouTube."
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
            return f"Searching for {args.get('query', '')}."
        return "Executing command."
