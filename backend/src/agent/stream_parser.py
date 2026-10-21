"""Stream parsing utilities for real-time sentence detection and tool collection."""

import json
import re
from typing import Any, Callable, List, Optional
from src.tools.models import ToolCall

FOLLOWUP_TAG_REGEX = re.compile(
    r"<\s*follow_?up(?:\s*\/|\s*>.*?<\/\s*follow_?up\s*|\s*\/?>)",
    re.IGNORECASE,
)
XML_TAG_REGEX = re.compile(r"<[^>]+>")


class StreamingSentenceDetector:
    """Incrementally splits streamed tokens into complete, clean spoken sentences."""

    def __init__(
        self,
        on_sentence: Optional[Callable[[str], None]] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.on_sentence = on_sentence
        self.on_token = on_token
        self.content_tokens: List[str] = []
        self.sentence_buffer: List[str] = []
        self.emitted_sentences: List[str] = []

    def feed_token(self, token: str) -> None:
        """Process a newly arrived streaming content token."""
        if not token:
            return

        self.content_tokens.append(token)
        self.sentence_buffer.append(token)

        if callable(self.on_token):
            self.on_token(token)

        # Detect sentence boundary characters (. ! ? \n)
        if any(p in token for p in (".", "!", "?", "\n")):
            buf_text = "".join(self.sentence_buffer)
            while True:
                match = re.search(r"^([\s\S]*?[.!?\n])(\s+[\s\S]*|$)", buf_text)
                if match and match.group(1).strip():
                    raw_sentence = match.group(1).strip()
                    buf_text = match.group(2).lstrip()

                    clean = self.clean_text(raw_sentence)
                    if clean:
                        self.emitted_sentences.append(clean)
                        if callable(self.on_sentence):
                            self.on_sentence(clean)
                else:
                    break
            self.sentence_buffer = [buf_text] if buf_text else []

    def flush(self) -> str:
        """Flushes any remaining text in the sentence buffer."""
        remaining_raw = "".join(self.sentence_buffer).strip()
        self.sentence_buffer.clear()
        clean = ""
        if remaining_raw:
            clean = self.clean_text(remaining_raw)
            if clean:
                self.emitted_sentences.append(clean)
                if callable(self.on_sentence):
                    self.on_sentence(clean)
        return clean

    @property
    def full_raw_text(self) -> str:
        return "".join(self.content_tokens).strip()

    @property
    def full_clean_text(self) -> str:
        return self.clean_text(self.full_raw_text)

    @property
    def has_followup(self) -> bool:
        return bool(FOLLOWUP_TAG_REGEX.search(self.full_raw_text))

    @staticmethod
    def clean_text(text: str) -> str:
        clean = FOLLOWUP_TAG_REGEX.sub("", text)
        clean = XML_TAG_REGEX.sub("", clean)
        return clean.strip()


class StreamingToolCollector:
    """Accumulates and parses streaming delta tool calls into validated ToolCall objects."""

    def __init__(self) -> None:
        self._tool_calls_dict: dict[int, dict[str, str]] = {}

    def feed_delta_tool_calls(self, delta_tool_calls: Any) -> None:
        """Accumulates tool call fragments from a streaming delta."""
        if not delta_tool_calls:
            return

        for tc in delta_tool_calls:
            idx = getattr(tc, "index", 0)
            if idx not in self._tool_calls_dict:
                self._tool_calls_dict[idx] = {
                    "name": tc.function.name or "" if getattr(tc, "function", None) else "",
                    "arguments": tc.function.arguments or "" if getattr(tc, "function", None) else "",
                }
            else:
                func = getattr(tc, "function", None)
                if func:
                    if func.name:
                        self._tool_calls_dict[idx]["name"] += func.name
                    if func.arguments:
                        self._tool_calls_dict[idx]["arguments"] += func.arguments

    def collect(self) -> List[ToolCall]:
        """Finalizes accumulated tool fragments into ToolCall instances."""
        collected: List[ToolCall] = []
        for idx in sorted(self._tool_calls_dict.keys()):
            item = self._tool_calls_dict[idx]
            t_name = item.get("name", "").strip()
            t_args_str = item.get("arguments", "")
            try:
                t_args = json.loads(t_args_str) if t_args_str else {}
            except Exception:
                t_args = {}
            if t_name:
                collected.append(ToolCall(name=t_name, args=t_args))
        return collected
