"""
Test script for Headless Web Search (Serper Google Search API with fallbacks).
Verifies that web queries return concise spoken answers without opening a browser window.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.core.config import config
from src.tools.handlers.web_search import execute as execute_web_search

def test_headless_search():
    print("=" * 65)
    print("  Testing Headless Web Search (Serper & Fallbacks)")
    has_serper = bool(config.search.serper_api_key and config.search.serper_api_key.strip())
    print(f"  Serper API Key: {'Configured (Live Google Search)' if has_serper else 'Not set (Using DDG/Wikipedia fallback)'}")
    print("=" * 65)

    test_queries = [
        "What is the capital of France?",
        "latest news about Tesla",
        "who is the CEO of Microsoft",
    ]

    for q in test_queries:
        print(f"\n[QUERY]: \"{q}\"")
        res = execute_web_search(q)
        print(f"  -> Success:        {res.success}")
        print(f"  -> Action:         {res.action}")
        print(f"  -> Message:        {res.message}")
        print(f"  -> Spoken Answer:  \"{res.spoken_override}\"")
        assert res.success is True
        assert res.spoken_override is not None and len(res.spoken_override) > 0

    print("\n" + "=" * 65)
    print("[SUCCESS] All headless web search tests passed successfully!")
    print("=" * 65)

if __name__ == "__main__":
    test_headless_search()
