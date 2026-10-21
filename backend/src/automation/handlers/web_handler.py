"""Web search handler supporting Serper (Google Search API), headless retrieval, and spoken summaries."""

import json
import logging
import re
import urllib.parse
import urllib.request
import webbrowser
from typing import Optional
from src.core.config import config
from src.core.messages import ActionMessages, ErrorMessages
from src.automation.models import ExecutionResult

logger = logging.getLogger(__name__)


class WebHandler:
    """Handles web search queries: Serper Google API, headless fallback, and YouTube routing."""

    @classmethod
    def headless_search(cls, query: str) -> ExecutionResult:
        """
        Headlessly searches the web for answers/news without opening a browser window.
        Uses Serper (Google Search API) if configured, with DuckDuckGo and Wikipedia fallback.
        Returns the concise spoken summary in `spoken_override` and full snippets in `data`.
        """
        clean_q = query.strip()
        logger.info("Executing headless web search for: '%s'", clean_q)

        summary: Optional[str] = None

        # 1. Primary: Serper (Google Search API) if API key is present
        serper_key = config.search.serper_api_key
        if serper_key and serper_key.strip():
            summary = cls._search_via_serper(clean_q, serper_key.strip())

        # 2. Fallback: DuckDuckGo Search library (DDGS)
        if not summary:
            summary = cls._search_via_ddgs(clean_q)

        # 3. Fallback: DuckDuckGo HTML endpoint
        if not summary:
            summary = cls._search_via_ddg_html(clean_q)

        # 4. Fallback: DuckDuckGo Instant Answer API
        if not summary:
            summary = cls._search_via_ddg_api(clean_q)

        # 5. Fallback: Wikipedia Summary API
        if not summary:
            summary = cls._search_via_wikipedia(clean_q)

        if summary:
            return ExecutionResult(
                success=True,
                action="web_search",
                message=ActionMessages.WEB_SEARCH_RETRIEVED.format(query=clean_q),
                spoken_override=summary,
                data={"query": clean_q, "snippets": summary},
            )

        # If all headless searches find nothing, return informative speech rather than silent browser popup
        return ExecutionResult(
            success=False,
            action="web_search",
            message=f"No online results found for '{clean_q}'.",
            spoken_override="Couldn't find anything on that right now.",
            data={"query": clean_q, "snippets": ""},
        )

    @classmethod
    def _search_via_serper(cls, query: str, api_key: str) -> Optional[str]:
        """
        Query Google Serper API (https://google.serper.dev/search).
        Extracts Google answerBox, knowledgeGraph, or top organic search snippets.
        """
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": 3}).encode("utf-8")
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            }
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # 1. Check Google answerBox (instant direct answers like weather, calculations, stock, facts)
            answer_box = data.get("answerBox")
            if answer_box:
                answer = answer_box.get("answer") or answer_box.get("snippet") or answer_box.get("title")
                if answer:
                    logger.info("Serper matched Google answerBox.")
                    return cls._clean_spoken_summary(str(answer))

            # 2. Check Google knowledgeGraph (people, companies, places, definitions)
            kg = data.get("knowledgeGraph")
            if kg:
                desc = kg.get("description") or kg.get("snippet")
                if desc:
                    title = kg.get("title", "")
                    text = f"{title}: {desc}" if title and not desc.startswith(title) else desc
                    logger.info("Serper matched Google knowledgeGraph.")
                    return cls._clean_spoken_summary(text)

            # 3. Check Google organic search snippets
            organic = data.get("organic", [])
            snippets = []
            for item in organic[:2]:
                snippet = item.get("snippet", "").strip()
                if snippet:
                    snippets.append(snippet)

            if snippets:
                logger.info("Serper matched %d organic snippets.", len(snippets))
                combined = " ".join(snippets)
                return cls._clean_spoken_summary(combined)

        except Exception as e:
            logger.warning("Serper Google search failed: %s. Using local fallback.", e)
        return None

    @classmethod
    def _search_via_ddgs(cls, query: str) -> Optional[str]:
        """Search using duckduckgo_search library."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                if any(w in query.lower() for w in ("news", "latest", "update", "today")):
                    try:
                        news_results = list(ddgs.news(query, max_results=3))
                        if news_results:
                            snippets = [r.get("body", "").strip() for r in news_results if r.get("body")]
                            if snippets:
                                return cls._clean_spoken_summary(" ".join(snippets[:2]))
                    except Exception:
                        pass

                results = list(ddgs.text(query, max_results=3))
                if results:
                    snippets = [r.get("body", "").strip() for r in results if r.get("body")]
                    if snippets:
                        combined = " ".join(snippets[:2])
                        return cls._clean_spoken_summary(combined)
        except Exception as e:
            logger.debug("DDGS search failed: %s", e)
        return None

    @classmethod
    def _search_via_ddg_html(cls, query: str) -> Optional[str]:
        """Direct HTTP search using DuckDuckGo HTML without external library dependencies."""
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            raw_snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, flags=re.DOTALL)
            clean_snippets = []
            for s in raw_snippets[:3]:
                text = re.sub(r"<[^>]+>", "", s)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    clean_snippets.append(text)
            if clean_snippets:
                return cls._clean_spoken_summary(" ".join(clean_snippets[:2]))
        except Exception as e:
            logger.debug("DDG HTML search fallback failed: %s", e)
        return None

    @classmethod
    def _search_via_ddg_api(cls, query: str) -> Optional[str]:
        """Search using DuckDuckGo Instant Answer JSON API."""
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": "DesktopHandsfreeAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            abstract = data.get("AbstractText", "").strip()
            if abstract:
                return cls._clean_spoken_summary(abstract)

            answer = data.get("Answer", "").strip()
            if answer:
                return cls._clean_spoken_summary(answer)

            related = data.get("RelatedTopics", [])
            for item in related:
                text = item.get("Text", "").strip()
                if text:
                    return cls._clean_spoken_summary(text)
        except Exception as e:
            logger.debug("DuckDuckGo API fallback failed: %s", e)
        return None

    @classmethod
    def _search_via_wikipedia(cls, query: str) -> Optional[str]:
        """Retrieve top summary snippet from Wikipedia REST API."""
        try:
            clean_topic = re.sub(r"^(?:who is|what is|tell me about|define|latest news on)\s+", "", query, flags=re.IGNORECASE).strip()
            encoded = urllib.parse.quote(clean_topic)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            req = urllib.request.Request(url, headers={"User-Agent": "DesktopHandsfreeAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            extract = data.get("extract", "").strip()
            if extract:
                return cls._clean_spoken_summary(extract)
        except Exception as e:
            logger.debug("Wikipedia fallback failed: %s", e)
        return None

    @staticmethod
    def _clean_spoken_summary(text: str, max_sentences: int = 2) -> str:
        """Cleans and shortens web snippet for natural, snappy TTS speech."""
        cleaned = re.sub(r"https?://\S+", "", text)
        cleaned = re.sub(r"\[\d+\]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Split into sentences and take top 2
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        selected = sentences[:max_sentences]
        result = " ".join(selected).strip()

        if len(result) > 280:
            result = result[:277] + "..."
        return result

    @classmethod
    def open_youtube_playback(cls, query: str) -> ExecutionResult:
        """Opens YouTube search/playback in the default web browser."""
        clean_q = query.strip()
        for filler in ("play on youtube", "on youtube", "play", "youtube", "about"):
            clean_q = re.sub(re.escape(filler), "", clean_q, flags=re.IGNORECASE).strip()

        if not clean_q:
            url = "https://www.youtube.com"
            msg = ActionMessages.YOUTUBE_OPENED
        else:
            encoded = urllib.parse.quote_plus(clean_q)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            msg = ActionMessages.YOUTUBE_SEARCH_OPENED.format(query=clean_q)

        try:
            webbrowser.open(url)
            return ExecutionResult(
                success=True,
                action="web_search",
                message=msg,
            )
        except Exception as e:
            logger.error("Failed to open YouTube: %s", e)
            return ExecutionResult(
                success=False,
                action="web_search",
                message=ErrorMessages.BROWSER_OPEN_FAILED.format(error=e),
            )

    @classmethod
    def open_browser_search(cls, query: str) -> ExecutionResult:
        """Fallback: opens Google search in default web browser."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        try:
            webbrowser.open(url)
            return ExecutionResult(
                success=True,
                action="web_search",
                message=ActionMessages.GOOGLE_SEARCH_OPENED.format(query=query),
            )
        except Exception as e:
            logger.error("Failed to open browser: %s", e)
            return ExecutionResult(
                success=False,
                action="web_search",
                message=ErrorMessages.BROWSER_OPEN_FAILED.format(error=e),
            )

    @classmethod
    def search(cls, query: str, raw_query: str = "") -> ExecutionResult:
        """Unified search router."""
        combined = f"{query} {raw_query}".lower()
        if any(w in combined for w in ("youtube", "video", "song", "gaana", "play ")):
            return cls.open_youtube_playback(query)
        return cls.headless_search(query)
