"""Unit & integration test for IntentDispatcher using OpenAI-compatible LLM."""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.agent.brain import LLMBrain
from src.automation.executor import ActionExecutor
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - LLM Brain & Tool Collector Test")
    print(f"  Target LLM: {config.llm.model} @ {config.llm.base_url}")
    print("=" * 65)

    brain = LLMBrain()
    executor = ActionExecutor()

    test_queries = [
        "Hello there!",
        "Open Google Chrome please",
        "Set master volume to 40 percent",
        "Pause the music",
        "What time is it right now?",
        "YouTube par Arijit Singh ke gaane chalao",
        "open youtube and such for dilljit dosans.",
        "Open chrome and search for Tesla new car.",
        "Who is the CEO of Google?",
    ]

    for q in test_queries:
        print(f"\n[QUERY]: \"{q}\"")
        print("  -> Streaming Tokens: ", end="", flush=True)

        early_reply_captured = None

        def on_reply(text: str) -> None:
            nonlocal early_reply_captured
            early_reply_captured = text

        resp = brain.process_command(
            q,
            on_reply_ready=on_reply,
            on_token=lambda tok: print(tok, end="", flush=True),
        )
        print()  # newline
        print(f"  -> Early Reply Ready: \"{early_reply_captured}\"")
        print(f"  -> Spoken Reply:     \"{resp.spoken_reply}\"")
        print(f"  -> Tool Calls:       {[(tc.name, tc.args) for tc in resp.tool_calls]}")

        # Direct execution via ActionExecutor
        if resp.tool_calls:
            results = executor.execute_tools(resp.tool_calls)
            for r in results:
                print(f"  -> Executed:         {r.action} -> {r.message} (Success: {r.success})")
        else:
            print("  -> (No tools called - direct conversation)")


    print("\n" + "=" * 65)
    print("[SUCCESS] Intent Dispatcher test complete!")
    print("=" * 65)

if __name__ == "__main__":
    main()
