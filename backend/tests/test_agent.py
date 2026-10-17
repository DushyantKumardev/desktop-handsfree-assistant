"""Unit & integration test for IntentDispatcher using OpenAI-compatible LLM."""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.agent.dispatcher import IntentDispatcher
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Intent Dispatcher Test")
    print(f"  Target LLM: {config.llm.model} @ {config.llm.base_url}")
    print("=" * 65)

    dispatcher = IntentDispatcher()

    test_queries = [
        "Open Google Chrome please",
        "What time is it right now?",
        "YouTube par Arijit Singh ke gaane chalao",
        "Open Notepad and calculator",
        "Who is the CEO of Google?",
    ]

    for q in test_queries:
        print(f"\n[QUERY]: \"{q}\"")
        print("  -> Streaming Tokens: ", end="", flush=True)

        early_reply_captured = None

        def on_reply(text: str) -> None:
            nonlocal early_reply_captured
            early_reply_captured = text

        res = dispatcher.process_command(
            q,
            on_reply_ready=on_reply,
            on_token=lambda tok: print(tok, end="", flush=True),
        )
        print()  # newline
        print(f"  -> Early Reply Ready: \"{early_reply_captured}\"")
        print(f"  -> Action:           {res.action}")
        print(f"  -> Target:           {res.target}")
        print(f"  -> Final Reply:      \"{res.speech_reply}\"")


    print("\n" + "=" * 65)
    print("[SUCCESS] Intent Dispatcher test complete!")
    print("=" * 65)

if __name__ == "__main__":
    main()
