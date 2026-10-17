"""Tool for opening desktop applications and site shortcuts."""

from typing import Any
from src.automation.handlers.app_handler import AppHandler
from src.automation.models import ExecutionResult

DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_app",
        "description": "Open or launch any desktop application, website, or site shortcut (e.g. Chrome, YouTube, Notepad, VS Code, Spotify, Calculator, Terminal).",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the application or website to open, e.g. 'chrome', 'youtube', 'notepad', 'vscode', 'spotify'",
                }
            },
            "required": ["app_name"],
        },
    },
}


def execute(app_name: str) -> ExecutionResult:
    """Launch the requested application or site."""
    return AppHandler.open_app(app_name)
