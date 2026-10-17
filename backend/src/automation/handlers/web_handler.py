"""Web search handler for Google and YouTube."""

import logging
import re
import urllib.parse
import webbrowser
from src.automation.models import ExecutionResult

logger = logging.getLogger(__name__)


class WebHandler:
    """Handles web search queries, YouTube routing, and filler word stripping."""

    @staticmethod
    def search(query: str, raw_query: str = "") -> ExecutionResult:
        """Opens a web search query in Google or YouTube in the default browser."""
        target_text = (query or "").strip()
        full_text = (raw_query or "").strip()

        combined = f"{target_text} {full_text}".lower()
        is_youtube = any(k in combined for k in ("youtube", "video", "music", "song", "gaana", "play"))

        if is_youtube:
            clean_q = target_text or full_text
            for filler in (
                "alexa", "open youtube and search for", "search youtube about",
                "search youtube for", "search youtube", "open youtube",
                "play on youtube", "on youtube", "search for", "search",
                "play", "youtube", "about"
            ):
                clean_q = re.sub(re.escape(filler), "", clean_q, flags=re.IGNORECASE).strip()

            clean_q = clean_q.strip()
            if not clean_q:
                url = "https://www.youtube.com"
                msg = "Opened YouTube in browser."
            else:
                encoded = urllib.parse.quote_plus(clean_q)
                url = f"https://www.youtube.com/results?search_query={encoded}"
                msg = f"Opened YouTube search for '{clean_q}'."
        else:
            search_query = target_text or full_text
            encoded = urllib.parse.quote_plus(search_query)
            url = f"https://www.google.com/search?q={encoded}"
            msg = f"Opened Google search for '{search_query}'."

        try:
            webbrowser.open(url)
            return ExecutionResult(
                success=True,
                action="web_search",
                message=msg,
            )
        except Exception as e:
            logger.error("Failed to open web search: %s", e)
            return ExecutionResult(
                success=False,
                action="web_search",
                message=f"Could not open browser: {e}",
            )
