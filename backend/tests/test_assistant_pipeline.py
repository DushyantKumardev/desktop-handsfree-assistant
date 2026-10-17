"""Complete voice loop with LLM brain: WakeWord -> VAD -> STT -> LLM Intent -> Neural TTS."""

import sys
import threading
import time
from pathlib import Path
from typing import Optional



# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.audio.capture import AudioCapture
from src.audio.recorder import AudioRecorder
from src.audio.feedback import SoundFeedback
from src.wakeword.detector import WakeWordDetector
from src.stt.transcriber import STTTranscriber
from src.agent.dispatcher import IntentDispatcher
from src.automation.executor import ActionExecutor
from src.tts.synthesizer import TTSSynthesizer
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Complete LLM & Action Voice Loop")
    print(f"  Wake Word:  {config.wakeword.models}")
    print(f"  STT:        Faster-Whisper ({config.stt.model_size})")
    print(f"  LLM Brain:  {config.llm.model} @ {config.llm.base_url}")
    print(f"  TTS Voice:  {config.tts.voice}")
    print("=" * 65)

    print("\n[+] Initializing pipeline components...")
    mic = AudioCapture()
    detector = WakeWordDetector()
    recorder = AudioRecorder()
    sounds = SoundFeedback()
    stt = STTTranscriber()
    agent = IntentDispatcher()
    executor = ActionExecutor()
    tts = TTSSynthesizer()

    is_wake_word_triggered = False

    def on_wake(model_name: str, confidence: float) -> None:
        nonlocal is_wake_word_triggered
        is_wake_word_triggered = True

    detector.on_detection = on_wake
    detector.start_listening(mic)
    mic.start()

    print("\n" + "=" * 65)
    print("  * ASSISTANT IS LIVE AND LISTENING *")
    print("  1. Say: 'Alexa'")
    print("  2. Speak your command after the chime (e.g. 'Open Chrome', 'What time is it?')")
    print("  3. Assistant executes action on your desktop and speaks back!")
    print("  (Press Ctrl+C to stop)")
    print("=" * 65)

    try:
        while True:
            # Clean detector state and mic queue before waiting for wake word
            time.sleep(0.4)
            mic.flush_queue()
            detector.reset()
            is_wake_word_triggered = False

            detector.start_listening(mic)
            print("\n[IDLE] Waiting for wake word ('Alexa')...")

            while not is_wake_word_triggered:
                time.sleep(0.05)

            # 1. Wake word triggered - play start chime
            detector.stop_listening()
            print("\n>>> [WAKE WORD DETECTED!]")
            sounds.play_start()
            mic.flush_queue()

            # 2. Record command with VAD
            print("[LISTENING] Speak now...")
            command_audio = recorder.record_phrase(
                mic,
                on_speech_start=lambda: print("  [*] Voice activity detected! [Speaking] ", end="", flush=True),
                on_speech_chunk=lambda energy: print(".", end="", flush=True),
            )
            print()
            sounds.play_stop(wait=False)

            # 3. Transcribe audio to text
            print("[+] Transcribing speech...")
            t0 = time.time()
            user_text = stt.transcribe(command_audio)
            stt_latency = time.time() - t0
            print(f"  >>> [USER SAID]: \"{user_text}\" ({stt_latency:.2f}s)")

            if not user_text:
                tts.speak("I could not hear anything.")
                time.sleep(0.5)
                mic.flush_queue()
                detector.reset()
                continue

            # 4. LLM processes intent & response with live token streaming
            print(f"[+] Thinking with LLM ({config.llm.model}): ", end="", flush=True)
            t1 = time.time()
            early_spoken = False
            tts_thread: Optional[threading.Thread] = None

            def on_reply_ready(early_reply: str) -> None:
                nonlocal early_spoken, tts_thread
                # If command is asking for time, let ActionExecutor provide the exact local clock time
                if any(w in user_text.lower() for w in ("time", "samay", "baj", "waqt")):
                    return
                if not early_spoken and early_reply:
                    early_spoken = True
                    print(f"\n[+] Speaking early status in background: \"{early_reply}\"")
                    # Run speech in background so token stream finishes in parallel without 10s wait!
                    tts_thread = threading.Thread(target=tts.speak, args=(early_reply,), daemon=True)
                    tts_thread.start()

            intent = agent.process_command(
                user_text,
                on_reply_ready=on_reply_ready,
                on_token=lambda tok: print(tok, end="", flush=True),
            )
            print()  # newline after live streaming tokens
            llm_latency = time.time() - t1

            print(f"  >>> [ACTION]:    {intent.action}")
            print(f"  >>> [TARGET]:    {intent.target}")
            print(f"  >>> [LLM REPLY]: \"{intent.speech_reply}\" ({llm_latency:.2f}s)")

            # 5. Execute action on desktop OS concurrently
            exec_res = executor.execute(intent)
            print(f"  >>> [EXECUTION]: {exec_res.message} (Success: {exec_res.success})")

            # 6. Final speech synchronization
            if exec_res.spoken_override:
                if tts_thread and tts_thread.is_alive():
                    tts_thread.join()
                print(f"[+] Speaking response: \"{exec_res.spoken_override}\"")
                tts.speak(exec_res.spoken_override)
            elif not early_spoken:
                speech_to_speak = intent.speech_reply
                print(f"[+] Speaking response: \"{speech_to_speak}\"")
                tts.speak(speech_to_speak)
            elif tts_thread and tts_thread.is_alive():
                # Wait for early speech to finish before reopening mic
                tts_thread.join()


            # Cooldown: wait for audio echo to fade and flush mic buffer
            time.sleep(0.5)
            mic.flush_queue()
            detector.reset()
            is_wake_word_triggered = False

            print("[SUCCESS] Command finished! Ready for next wake word.")

    except KeyboardInterrupt:
        print("\n[+] Exiting assistant loop...")
    finally:
        detector.stop_listening()
        mic.stop()

if __name__ == "__main__":
    main()
