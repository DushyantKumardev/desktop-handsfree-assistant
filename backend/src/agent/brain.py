import datetime
import json
import logging
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

            # If LLM called tools without speaking connecting text, provide default phrase
            if collected_tools and not clean_speech:
                first_tool = collected_tools[0]
                clean_speech = self._generate_default_phrase(first_tool.name, first_tool.args)
                if clean_speech:
                    if callable(on_sentence_ready):
                        on_sentence_ready(clean_speech)
                    if not first_sentence_emitted and callable(on_reply_ready):
                        on_reply_ready(clean_speech)

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
    def _generate_default_phrase(tool_name: str, args: dict[str, Any]) -> str:
        """Fallback phrase if model was silent when requesting a tool."""
        if tool_name == "open_app":
            return ToolDefaultPhrases.OPEN_APP.format(app=args.get("app_name", "application"))
        elif tool_name == "play_media":
            q = args.get("query", "")
            return ToolDefaultPhrases.PLAY_MEDIA.format(query=q) if q else ToolDefaultPhrases.PLAY_MEDIA_DEFAULT
        elif tool_name == "media_control":
            return ToolDefaultPhrases.MEDIA_CONTROL_NEXT if args.get("command") == "next_track" else ToolDefaultPhrases.MEDIA_CONTROL_TOGGLE
        elif tool_name == "set_volume":
            return ToolDefaultPhrases.SET_VOLUME.format(level=args.get("level", 50))
        elif tool_name == "adjust_volume":
            return ToolDefaultPhrases.ADJUST_VOLUME.format(direction=args.get("direction", "up"))
        elif tool_name == "mute_volume":
            return ToolDefaultPhrases.MUTE_VOLUME
        elif tool_name == "lock_computer":
            return ToolDefaultPhrases.LOCK_COMPUTER
        elif tool_name == "web_search":
            q = args.get("query", "")
            return ToolDefaultPhrases.WEB_SEARCH.format(query=q) if q else ToolDefaultPhrases.WEB_SEARCH_DEFAULT
        elif tool_name == "set_speaking_speed":
            # Let the tool's spoken override speak at the new speed directly
            return ""
        elif tool_name == "schedule_action":
            return ToolDefaultPhrases.SCHEDULE_ACTION
        elif tool_name == "cancel_schedule":
            return ToolDefaultPhrases.CANCEL_SCHEDULE
        return AssistantResponses.DEFAULT_FALLBACK
