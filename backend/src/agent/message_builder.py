"""Helper for preparing LLM messages and provider-specific configurations."""

from typing import Any, Dict, List
from src.core.constants import get_system_prompt


class MessageBuilder:
    """Builds conversation payloads and provider configuration kwargs."""

    @staticmethod
    def build_chat_messages(
        user_query: str,
        conversation_history: List[Dict[str, str]],
        history_turns: int = 4,
    ) -> List[Dict[str, Any]]:
        """Constructs prompt payload with dynamic system prompt, recent context, and user query."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": get_system_prompt()},
        ]
        if history_turns > 0 and conversation_history:
            messages.extend(conversation_history[-history_turns:])
        messages.append({"role": "user", "content": user_query})
        return messages

    @staticmethod
    def get_provider_extra_body(base_url: str, reasoning_effort: str = "low") -> Dict[str, Any]:
        """Suppresses unwanted thinking/reasoning latency across various providers."""
        extra: Dict[str, Any] = {}
        base_lower = base_url.lower()

        if "openrouter" in base_lower:
            extra.update({
                "reasoning": {"max_tokens": 0},
                "thinking": {"type": "disabled"},
            })
            if reasoning_effort:
                extra["reasoning_effort"] = reasoning_effort
        elif "ollama" in base_lower or "11434" in base_lower:
            extra.update({
                "think": False,
                "reasoning_effort": "none",
            })

        return extra
