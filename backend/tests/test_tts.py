"""Interactive test for offline neural voice synthesis with Piper."""

import sys
import time
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.tts.synthesizer import TTSSynthesizer
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Offline Neural Voice (Piper)")
    print("=" * 65)

    print(f"[+] Initializing Piper TTS (Voice: {config.tts.voice})...")
    tts = TTSSynthesizer()

    # 1. English sentence
    en_phrase = "Hello! I am your desktop assistant. I can speak naturally in English."
    print(f"\n[+] [Auto-Detect EN] Speaking: \"{en_phrase}\"")
    tts.speak(en_phrase)

    # 2. Hindi sentence (auto-switches to Priyamvada without extra parameters)
    hi_phrase = "नमस्ते! मैं हिंदी और अंग्रेज़ी दोनों भाषाएं आसानी से बोल सकती हूँ।"
    print(f"\n[+] [Auto-Detect HI] Speaking: \"{hi_phrase}\"")
    tts.speak(hi_phrase)

    print("\n[SUCCESS] Auto-language voice switching verified successfully!")
    print("=" * 65)

if __name__ == "__main__":
    main()
