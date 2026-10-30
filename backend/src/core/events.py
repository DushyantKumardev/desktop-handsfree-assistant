"""
Real-time Event Emitter for Assistant Status & Tool Updates.
Allows any tool (e.g. web search, scheduler, system control) or agent component
to emit status messages directly to the UI overlay.
"""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Type for status listeners: (message: str, tool_name: Optional[str]) -> None
StatusListener = Callable[[str, Optional[str]], None]

_status_listeners: list[StatusListener] = []


def on_status(listener: StatusListener) -> None:
    """Register a callback listener for status updates."""
    if listener not in _status_listeners:
        _status_listeners.append(listener)


def off_status(listener: StatusListener) -> None:
    """Unregister a status listener callback."""
    if listener in _status_listeners:
        _status_listeners.remove(listener)


def emit_status(message: str, tool_name: Optional[str] = None) -> None:
    """
    Broadcasts a real-time status message to all registered listeners and WebSocket server.
    Example:
        emit_status("Searching Google...", tool_name="web_search")
    """
    logger.debug("Status update [%s]: %s", tool_name or "assistant", message)

    # 1. Notify Python-level listeners
    for listener in list(_status_listeners):
        try:
            listener(message, tool_name)
        except Exception as e:
            logger.error("Error in status listener: %s", e)

    # 2. Forward to WebSocket server if available
    try:
        from src.server.ws_server import ws_server
        ws_server.broadcast_status(message, tool_name=tool_name)
    except Exception as e:
        logger.debug("Could not broadcast status over WS: %s", e)
