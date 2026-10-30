"""
The Assistant's LLM Brain: streams spoken conversational replies and collects native tool calls.
"""

import logging
from typing import Any, Callable, Optional
from openai import OpenAI
from src.core.config import LLMConfig, config
from src.core.messages import AssistantResponses, ErrorMessages
from src.tools import DESKTOP_TOOLS, LLMResponse
from src.agent.stream_parser import StreamingSentenceDetector, StreamingToolCollector
from src.agent.message_builder import MessageBuilder

logger = logging.getLogger(__name__)


class LLMBrain:
    """The Assistant's LLM Brain: orchestrates streaming completions, real-time audio, and native tools."""

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
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> LLMResponse:
        """
        Processes user query with the LLM.
        - Streams spoken sentences dynamically via on_sentence_ready as they complete.
        - Detects <followup/> XML tag to automatically trigger listening cycle.
        - Collects any requested ToolCalls and returns LLMResponse.
        """
        if not user_query.strip():
            return LLMResponse(
                spoken_reply=AssistantResponses.EMPTY_QUERY,
                tool_calls=[],
                raw_query="",
                needs_followup=False,
            )

        messages = MessageBuilder.build_chat_messages(
            user_query=user_query,
            conversation_history=self.conversation_history,
            history_turns=4,
        )

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "tools": DESKTOP_TOOLS,
            "tool_choice": "auto",
            "temperature": self.config.temperature,
            "stream": True,
        }
        if self.config.max_tokens and self.config.max_tokens > 0:
            request_kwargs["max_tokens"] = self.config.max_tokens

        extra_body = MessageBuilder.get_provider_extra_body(
            base_url=self.config.base_url,
            reasoning_effort=self.config.reasoning_effort or "low",
        )
        if extra_body:
            request_kwargs["extra_body"] = extra_body

        first_sentence_emitted = False

        def handle_sentence(sentence: str) -> None:
            if is_cancelled and is_cancelled():
                return
            nonlocal first_sentence_emitted
            if callable(on_sentence_ready):
                on_sentence_ready(sentence)
            if not first_sentence_emitted:
                first_sentence_emitted = True
                if callable(on_reply_ready):
                    on_reply_ready(sentence)

        sentence_detector = StreamingSentenceDetector(
            on_sentence=handle_sentence,
            on_token=on_token,
        )
        tool_collector = StreamingToolCollector()

        try:
            stream = self.client.chat.completions.create(**request_kwargs)

            for chunk in stream:
                if is_cancelled and is_cancelled():
                    logger.info("LLM generation cancelled by user.")
                    break
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                if delta.content:
                    sentence_detector.feed_token(delta.content)

                if delta.tool_calls:
                    tool_collector.feed_delta_tool_calls(delta.tool_calls)

            # Flush remaining tokens into final sentence
            sentence_detector.flush()

            clean_speech = sentence_detector.full_clean_text
            collected_tools = tool_collector.collect()

            if not clean_speech and not collected_tools:
                final_reply = AssistantResponses.EMPTY_QUERY
            else:
                final_reply = clean_speech

            # Store in conversation memory (only when not delegating to tools that synthesize their own answer)
            if not any(tc.name == "web_search" for tc in collected_tools) and final_reply:
                self.conversation_history.append({"role": "user", "content": user_query})
                self.conversation_history.append({"role": "assistant", "content": final_reply})
                if len(self.conversation_history) > 12:
                    self.conversation_history = self.conversation_history[-12:]

            return LLMResponse(
                spoken_reply=final_reply,
                tool_calls=collected_tools,
                raw_query=user_query,
                needs_followup=sentence_detector.has_followup,
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

    def synthesize_tool_answer(
        self,
        user_query: str,
        tool_name: str,
        tool_data: str,
        on_sentence_ready: Optional[Callable[[str], None]] = None,
        on_token: Optional[Callable[[str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        Synthesizes tool data (get_schedules, web_search, etc.) into a punchy, spoken conversational answer using the LLM.
        Streams sentence chunks to on_sentence_ready for real-time TTS playback.
        """
        if not tool_data or not tool_data.strip():
            fallback = "Couldn't find any information on that."
            if callable(on_sentence_ready):
                on_sentence_ready(fallback)
            return fallback

        system_instruction = (
            "You are the user's chill, sharp desktop companion. "
            "Use the provided tool findings to directly answer the user's question in your own natural words. "
            "Keep the answer to 1 or 2 punchy, spoken conversational sentences (under 35 words). "
            "Never use markdown, bullet points, numbered lists, asterisks, or quotes. "
            "Supports English, Hindi, and Hinglish seamlessly."
        )

        user_prompt = (
            f'User asked: "{user_query}"\n\n'
            f'Tool ({tool_name}) findings:\n{tool_data}\n\n'
            f"Spoken answer:"
        )

        messages = [
            {"role": "system", "content": system_instruction},
        ]
        if self.conversation_history:
            messages.extend(self.conversation_history[-2:])
        messages.append({"role": "user", "content": user_prompt})

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "stream": True,
        }
        if self.config.max_tokens and self.config.max_tokens > 0:
            request_kwargs["max_tokens"] = self.config.max_tokens

        extra_body = MessageBuilder.get_provider_extra_body(
            base_url=self.config.base_url,
            reasoning_effort=self.config.reasoning_effort or "low",
        )
        if extra_body:
            request_kwargs["extra_body"] = extra_body

        def handle_sentence(sentence: str) -> None:
            if is_cancelled and is_cancelled():
                return
            if callable(on_sentence_ready):
                on_sentence_ready(sentence)

        sentence_detector = StreamingSentenceDetector(
            on_sentence=handle_sentence,
            on_token=on_token,
        )

        try:
            stream = self.client.chat.completions.create(**request_kwargs)
            for chunk in stream:
                if is_cancelled and is_cancelled():
                    logger.info("Tool answer synthesis cancelled by user.")
                    break
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    sentence_detector.feed_token(delta.content)

            sentence_detector.flush()
            clean_reply = sentence_detector.full_clean_text

            if not clean_reply:
                clean_reply = tool_data[:200]
                if callable(on_sentence_ready):
                    on_sentence_ready(clean_reply)

            # Store in conversation memory
            self.conversation_history.append({"role": "user", "content": user_query})
            self.conversation_history.append({"role": "assistant", "content": clean_reply})
            if len(self.conversation_history) > 12:
                self.conversation_history = self.conversation_history[-12:]

            return clean_reply

        except Exception as e:
            logger.error("Tool answer synthesis failed: %s", e)
            fallback = tool_data[:200]
            if callable(on_sentence_ready):
                on_sentence_ready(fallback)
            return fallback

    def synthesize_search_answer(
        self,
        user_query: str,
        search_query: str,
        search_content: str,
        on_sentence_ready: Optional[Callable[[str], None]] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Web search synthesis alias delegating to synthesize_tool_answer."""
        return self.synthesize_tool_answer(
            user_query=user_query,
            tool_name="web_search",
            tool_data=f'Query "{search_query}": {search_content}',
            on_sentence_ready=on_sentence_ready,
            on_token=on_token,
        )
