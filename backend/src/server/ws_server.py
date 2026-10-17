"""
WebSocket Server for Desktop Handsfree Assistant.
Broadcasts engine events (wake word, transcription, LLM streaming, tools) to the frontend overlay.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger("ws_server")

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("Package 'websockets' not installed. Install via: pip install websockets")


class AssistantWSServer:
    """Ultra-fast, thread-safe WebSocket broadcast server for frontend overlay synchronization."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[Any] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
        self.on_trigger_listen: Optional[Callable[[], None]] = None
        self.on_cancel_requested: Optional[Callable[[], None]] = None

    def start(self) -> None:
        """Starts the WebSocket server in a background daemon thread."""
        if not HAS_WEBSOCKETS:
            print("[WS] 'websockets' library missing. Run: pip install websockets")
            return

        if self.running:
            return

        self.running = True
        self.server_thread = threading.Thread(target=self._run_event_loop, daemon=True, name="WSServerThread")
        self.server_thread.start()
        print(f"[+] WebSocket server started on ws://{self.host}:{self.port}")

    def _run_event_loop(self) -> None:
        """Runs the asyncio loop inside the dedicated thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def handler(websocket: Any):
            self.clients.add(websocket)
            logger.info("Frontend connected to WebSocket (%s)", websocket.remote_address)
            try:
                # Send immediate connection ack
                await websocket.send(json.dumps({
                    "type": "SERVER_STATE_CHANGE",
                    "payload": {"state": "idle"},
                    "timestamp": int(time.time() * 1000)
                }))

                async for raw_msg in websocket:
                    try:
                        msg = json.loads(raw_msg)
                        msg_type = msg.get("type")
                        if msg_type == "CLIENT_TRIGGER_LISTEN":
                            if self.on_trigger_listen:
                                self.on_trigger_listen()
                        elif msg_type == "CLIENT_CANCEL":
                            if self.on_cancel_requested:
                                self.on_cancel_requested()
                        elif msg_type == "PING":
                            await websocket.send(json.dumps({"type": "PONG", "timestamp": int(time.time() * 1000)}))
                    except Exception as err:
                        logger.error("Error processing client WS message: %s", err)
            except Exception as e:
                logger.debug("Client disconnected: %s", e)
            finally:
                self.clients.discard(websocket)

        async def serve():
            async with websockets.serve(handler, self.host, self.port):
                await asyncio.Future()  # run forever

        try:
            self.loop.run_until_complete(serve())
        except Exception as e:
            if self.running:
                logger.error("WebSocket server encountered error: %s", e)

    def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Thread-safe broadcast of a message to all connected frontend clients."""
        if not self.running or not self.loop or not self.clients:
            return

        message = json.dumps({
            "type": event_type,
            "payload": payload,
            "timestamp": int(time.time() * 1000)
        })

        async def _send_all():
            disconnected = set()
            for client in list(self.clients):
                try:
                    await client.send(message)
                except Exception:
                    disconnected.add(client)
            self.clients.difference_update(disconnected)

        asyncio.run_coroutine_threadsafe(_send_all(), self.loop)

    def broadcast_show_widget(self) -> None:
        """Signals the frontend overlay to pop up on screen."""
        self.broadcast("SERVER_SHOW_WIDGET", {})

    def broadcast_state(self, state: str, is_followup: bool = False) -> None:
        """Broadcasts state change: idle, listening, thinking, speaking."""
        self.broadcast("SERVER_STATE_CHANGE", {"state": state, "is_followup": is_followup})

    def broadcast_transcription(self, text: str, is_final: bool = True) -> None:
        """Broadcasts speech-to-text transcript."""
        self.broadcast("SERVER_TRANSCRIPTION", {"text": text, "is_final": is_final})

    def broadcast_stream_chunk(self, chunk: str, query: str = "") -> None:
        """Broadcasts real-time streaming LLM sentence or token chunk."""
        self.broadcast("SERVER_STREAM_CHUNK", {"chunk": chunk, "query": query})

    def broadcast_response_complete(self, query: str, content: str, needs_followup: bool = False) -> None:
        """Signals that speech and text generation is finished."""
        self.broadcast("SERVER_RESPONSE_COMPLETE", {
            "query": query,
            "content": content,
            "needs_followup": needs_followup,
        })

    def broadcast_notification(self, title: str, message: str, task_id: Optional[str] = None) -> None:
        """Broadcasts a notification event for native desktop toast display."""
        self.broadcast("SERVER_NOTIFICATION", {
            "title": title,
            "message": message,
            "taskId": task_id,
        })


# Global singleton instance
ws_server = AssistantWSServer()
