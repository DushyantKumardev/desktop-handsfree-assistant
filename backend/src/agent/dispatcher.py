"""Intent Dispatcher using OpenAI-compatible SDK with automatic local fallback."""

import json
import logging
import re
from typing import Callable, Optional
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
4. "system_control": User asks to adjust volume, media, or computer lock.
   - Adjust volume to specific percentage (e.g. "set volume to 45%", "volume 45", "volume 45 percent", "volume ko 50 karo") -> target: "volume_set:45"
   - Increase volume -> target: "volume_up"
   - Decrease volume -> target: "volume_down"
   - Mute or unmute -> target: "mute"
   - Pause or play media -> target: "pause"
   - Lock computer -> target: "lock"
5. "conversation": Questions, small talk, or general queries.
   target: null.


Output format (STRICT JSON ONLY, no markdown, no backticks):
{
  "reply": "<1 short, natural, friendly sentence to speak back to the user in the language they used>",
  "action": "<action_name>",
  "target": "<target_or_null>"
}

CRITICAL SPEED & BEHAVIOR RULE:
Output strictly the raw JSON object immediately.
Do NOT include any <think> tags, internal reasoning, explanation, or conversational markdown.
Begin your output immediately with the opening brace '{'.
"""


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

    def process_command(
        self,
        user_query: str,
        on_reply_ready: Optional[Callable[[str], None]] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> IntentResult:
        """
        Process user speech text using LLM with live token streaming.
        Emits on_reply_ready as soon as the reply sentence is generated.
        Falls back to rule-based parser if the LLM server is unreachable.
        """
        if not user_query.strip():
            return IntentResult(action="conversation", speech_reply="I did not catch that.", raw_query="")

        accumulated = ""
        reply_emitted = False
        early_reply = ""

        # 1. Build optimized request payload suppressing thinking delays
        request_kwargs = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
            "stream": True,
        }

        # Extra body for OpenRouter, Ollama, and Anthropic to eliminate reasoning latency
        extra_body = {
            "reasoning": {"max_tokens": 0},
            "thinking": {"type": "disabled"},
            "options": {"num_predict": self.config.max_tokens},
        }

        if self.config.reasoning_effort:
            if any(k in self.config.model.lower() for k in ("o1", "o3")):
                request_kwargs["reasoning_effort"] = self.config.reasoning_effort
            extra_body["reasoning_effort"] = self.config.reasoning_effort

        request_kwargs["extra_body"] = extra_body

        try:
            stream = self.client.chat.completions.create(**request_kwargs)

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue
                accumulated += delta
                if callable(on_token):
                    on_token(delta)

                # As soon as the "reply": "..." field is closed, emit early reply to start TTS!
                if not reply_emitted:
                    match = re.search(r'"reply"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', accumulated)
                    if match:
                        try:
                            early_reply = json.loads(f'"{match.group(1)}"')
                        except Exception:
                            early_reply = match.group(1)
                        reply_emitted = True
                        if callable(on_reply_ready) and early_reply:
                            on_reply_ready(early_reply)

            # Clean and parse completed JSON
            clean_json = re.sub(r"```(?:json)?|```", "", accumulated).strip()
            try:
                data = json.loads(clean_json)
            except json.JSONDecodeError:
                if not clean_json.endswith("}"):
                    clean_json += "}"
                data = json.loads(clean_json)

            speech_reply = data.get("reply") or early_reply or "I am on it."

            if not reply_emitted and callable(on_reply_ready) and speech_reply:
                on_reply_ready(speech_reply)

            return IntentResult(
                action=data.get("action", "conversation"),
                target=data.get("target"),
                speech_reply=speech_reply,
                raw_query=user_query,
            )

        except Exception as e:
            logger.warning("LLM inference failed (%s). Using local fallback parser.", e)
            res = self._fallback_rule_parser(user_query)
            if callable(on_reply_ready) and res.speech_reply:
                on_reply_ready(res.speech_reply)
            return res

    def _fallback_rule_parser(self, query: str) -> IntentResult:
        """Fast offline rule-based parser when LLM is unavailable."""
        q = query.lower().strip()

        # Check for system controls (volume / mute / lock)
        vol_pct_match = re.search(r"\b(?:volume|awaz|sound)\s*(?:to|ko|at|=|pe)?\s*(\d{1,3})\s*%?", q)
        if not vol_pct_match:
            vol_pct_match = re.search(r"\b(?:set|karo|change)\s*(?:volume|awaz|sound)?\s*(?:to|ko|at)?\s*(\d{1,3})\s*%", q)
        if vol_pct_match:
            pct_val = max(0, min(100, int(vol_pct_match.group(1))))
            return IntentResult(
                action="system_control",
                target=f"volume_set:{pct_val}",
                speech_reply=f"Setting volume to {pct_val} percent.",
                raw_query=query,
            )

        if any(w in q for w in ("volume up", "awaz badhao", "louder")):
            return IntentResult(
                action="system_control",
                target="volume_up",
                speech_reply="Increasing volume.",
                raw_query=query,
            )
        if any(w in q for w in ("volume down", "awaz kam", "quieter")):
            return IntentResult(
                action="system_control",
                target="volume_down",
                speech_reply="Decreasing volume.",
                raw_query=query,
            )
        if any(w in q for w in ("mute", "unmute", "chup")):
            return IntentResult(
                action="system_control",
                target="mute",
                speech_reply="Toggling mute.",
                raw_query=query,
            )
        if any(w in q for w in ("lock computer", "lock pc", "lock screen")):
            return IntentResult(
                action="system_control",
                target="lock",
                speech_reply="Locking your computer.",
                raw_query=query,
            )

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
