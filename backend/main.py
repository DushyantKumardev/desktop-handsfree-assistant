"""
Desktop Handsfree Assistant - Main Starter.
Offline-first continuous voice assistant daemon.
"""

import logging
import signal
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Silence noisy background logs so terminal is clean and readable
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
for noisy_lib in ("httpcore", "httpcore2", "httpx", "openai", "urllib3", "piper", "src"):
    logging.getLogger(noisy_lib).setLevel(logging.WARNING)

from src.agent import HandsfreeAssistant


def main() -> None:
    """Initialize and start the voice assistant."""
    assistant = HandsfreeAssistant()

    # Graceful termination handlers
    def handle_signal(sig, frame):
        assistant.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    assistant.start()


if __name__ == "__main__":
    main()
