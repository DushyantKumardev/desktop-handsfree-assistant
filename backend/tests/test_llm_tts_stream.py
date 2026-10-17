"""
Interactive test script: End-to-end LLM Token Streaming -> Piper TTS Audio Streaming.
Measures total latency from command submission to first spoken audio.
"""

import sys
import time
import threading
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.agent.brain import LLMBrain
from src.tts.synthesizer import TTSSynthesizer
from src.core.config import config

def run_llm_tts_interactive():
    print("=" * 65)
    print("  Live LLM Streaming -> Real-Time Piper TTS Audio Pipeline")
    print("=" * 65)

    print(f"[*] Initializing Piper TTS ({config.tts.voice})...")
    tts = TTSSynthesizer()

    print(f"[*] Initializing LLM Brain ({config.llm.model})...")
    brain = LLMBrain()
    print("[+] Both engines initialized and ready!\n")

    sample_prompts = [
        "set volume to 40%",
        "what is the time right now",
        "open youtube and play lo-fi hip hop",
        "tell me a quick one-sentence joke about computers",
    ]

    print("Sample prompts to try:")
    for i, p in enumerate(sample_prompts, 1):
        print(f"  [{i}] {p}")
    print("  Or type any custom command (type 'exit' or 'q' to quit)\n")

    while True:
        try:
            user_input = input("User Command > ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            print("\nExiting live test.")
            break

        # Expand sample prompt shortcut
        if user_input.isdigit() and 1 <= int(user_input) <= len(sample_prompts):
            user_input = sample_prompts[int(user_input) - 1]
            print(f"Selected: \"{user_input}\"")

        print("\n" + "-" * 50)
        t_start = time.time()
        reply_received_time = None
        first_audio_time = None
        spoken_in_background = False
        tts_thread = None

        def on_reply_ready(early_reply: str) -> None:
            nonlocal reply_received_time, first_audio_time, spoken_in_background, tts_thread
            if not spoken_in_background and early_reply:
                spoken_in_background = True
                reply_received_time = time.time() - t_start
                print(f"\n[+] Early Speech Reply: \"{early_reply}\" (LLM emitted in: {reply_received_time:.2f}s)")

                def stream_speech():
                    nonlocal first_audio_time
                    first_audio_time = time.time() - t_start
                    print(f"[+] Audio stream playing! (End-to-end latency to speech: {first_audio_time:.2f}s)")
                    tts.speak(early_reply, stream=True)

                tts_thread = threading.Thread(target=stream_speech, daemon=True)
                tts_thread.start()

        print("[*] Streaming LLM tokens: ", end="", flush=True)
        llm_resp = brain.process_command(
            user_input,
            on_reply_ready=on_reply_ready,
            on_token=lambda tok: print(tok, end="", flush=True),
        )
        print() # Newline after token stream
        t_total_llm = time.time() - t_start
        print(f"  -> Spoken Reply: \"{llm_resp.spoken_reply}\"")
        print(f"  -> Tool Calls:   {[(tc.name, tc.args) for tc in llm_resp.tool_calls]}")
        print(f"  -> Total LLM stream duration: {t_total_llm:.2f}s")

        # Wait for TTS audio to finish playing if it was started
        if tts_thread and tts_thread.is_alive():
            print("[*] Waiting for voice playback to finish...")
            tts_thread.join()

        print("-" * 50 + "\n")

if __name__ == "__main__":
    run_llm_tts_interactive()
