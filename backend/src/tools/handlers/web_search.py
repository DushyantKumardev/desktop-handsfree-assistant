"""Tool for headless web search with direct spoken answers."""

from typing import Any
from src.automation.handlers.web_handler import WebHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Headlessly search the web for facts, latest news, weather, definitions, or questions. Returns a concise spoken answer without opening a browser window.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, question, or topic to search on the web",
                }
            },
            "required": ["query"],
        },
    },
}


def execute(query: str) -> ExecutionResult:
    """Perform headless web search and return spoken summary in spoken_override."""
    from src.core.events import emit_status
    emit_status("Searching Google...", tool_name="web_search")
    return WebHandler.headless_search(query)
