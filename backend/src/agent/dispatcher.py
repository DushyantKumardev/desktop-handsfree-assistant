"""Intent Dispatcher using OpenAI-compatible SDK with automatic local fallback."""

import json
import logging
import re
from typing import Optional
from openai import OpenAI
from src.core.config import LLMConfig, config
from .intent import IntentResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the intelligent brain of a desktop hands-free voice assistant.
If asked about your identity or creator, you are a desktop voice assistant created to help control and navigate the user's computer hands-free.
Your task is to analyze the user's spoken command (which may be in English, Hindi, or Hinglish) and return a strict JSON response.

Supported actions:
1. "open_app": User wants to open or launch an application (e.g., chrome, notepad, calculator, vscode, spotify).
   target: app name (e.g., "chrome", "notepad").
2. "web_search": User wants to search something or play something on YouTube/Google.
   target: search query.
3. "get_time": User asks for time or date.
   target: null.
4. "conversation": Questions, small talk, or general queries.
   target: null.

Output format (STRICT JSON ONLY, no markdown, no backticks):
{
  "action": "<action_name>",
  "target": "<target_or_null>",
  "reply": "<1 short, natural, friendly sentence to speak back to the user in the language they used>"
}"""


class IntentDispatcher:
    """Dispatches user transcribed text to an LLM to extract actions and generate voice replies."""

    def __init__(self, llm_config: Optional[LLMConfig] = None) -> None:
        self.config = llm_config or config.llm
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=10.0,
        )
        logger.info(
            "IntentDispatcher initialized with endpoint: %s (Model: %s)",
            self.config.base_url,
            self.config.model,
        )

    def process_command(self, user_query: str) -> IntentResult:
        """
        Process user speech text using LLM and return structured IntentResult.
        Falls back to rule-based parser if the LLM server is unreachable.
        """
        if not user_query.strip():
            return IntentResult(action="conversation", speech_reply="I did not catch that.", raw_query="")

        # 1. Try LLM inference
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_query},
                ],
                temperature=self.config.temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)

            return IntentResult(
                action=data.get("action", "conversation"),
                target=data.get("target"),
                speech_reply=data.get("reply", "I am on it."),
                raw_query=user_query,
            )

        except Exception as e:
            logger.warning("LLM inference failed (%s). Using local fallback parser.", e)
            return self._fallback_rule_parser(user_query)

    def _fallback_rule_parser(self, query: str) -> IntentResult:
        """Fast offline rule-based parser when LLM is unavailable."""
        q = query.lower().strip()

        # Check for open app
        open_match = re.search(r"\b(open|launch|start|kholo|chalao)\s+([a-zA-Z0-9_\-\s]+)", q)
        if open_match:
            app = open_match.group(2).strip()
            # Clean common filler words
            app = re.sub(r"\b(please|app|application|na)\b", "", app).strip()
            return IntentResult(
                action="open_app",
                target=app,
                speech_reply=f"Opening {app}.",
                raw_query=query,
            )

        # Check for time
        if any(w in q for w in ("time", "samay", "baj", "waqt")):
            return IntentResult(
                action="get_time",
                speech_reply="Checking the current time.",
                raw_query=query,
            )

        # Check for search / play
        search_match = re.search(r"\b(search|find|google|play|dhoondo)\s+(for\s+)?(.+)", q)
        if search_match:
            term = search_match.group(3).strip()
            return IntentResult(
                action="web_search",
                target=term,
                speech_reply=f"Searching for {term}.",
                raw_query=query,
            )

        return IntentResult(
            action="conversation",
            speech_reply=f"You said: {query}",
            raw_query=query,
        )
