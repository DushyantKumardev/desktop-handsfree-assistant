"""Tool for searching the web via Google."""

from typing import Any
from src.automation.handlers.web_handler import WebHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web on Google for questions, facts, news, websites, or products. Call this when user says 'search for X', 'open chrome and search for X', 'look up X', or 'google X'.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on Google",
                }
            },
            "required": ["query"],
        },
    },
}


def execute(query: str) -> ExecutionResult:
    """Perform Google search."""
    return WebHandler.search(query)
