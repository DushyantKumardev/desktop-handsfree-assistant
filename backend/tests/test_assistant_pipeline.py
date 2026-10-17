"""Complete voice loop with LLM brain: WakeWord -> VAD -> STT -> LLM Intent -> Neural TTS."""

import sys
import time
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.audio.capture import AudioCapture
from src.audio.recorder import AudioRecorder
from src.wakeword.detector import WakeWordDetector
from src.stt.transcriber import STTTranscriber
from src.agent.dispatcher import IntentDispatcher
from src.tts.synthesizer import TTSSynthesizer
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Complete LLM Voice Loop")
    print(f"  Wake Word:  {config.wakeword.models}")
    print(f"  STT:        Faster-Whisper ({config.stt.model_size})")
    print(f"  LLM Brain:  {config.llm.model} @ {config.llm.base_url}")
    print(f"  TTS Voice:  {config.tts.voice}")
    print("=" * 65)

    print("\n[+] Initializing pipeline components...")
    mic = AudioCapture()
    detector = WakeWordDetector()
    recorder = AudioRecorder()
    stt = STTTranscriber()
    agent = IntentDispatcher()
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
    print("  2. Speak your command or question (e.g. 'Open Chrome' or 'What is AI?')")
    print("  3. The LLM brain will understand, decide action, and speak back!")
    print("=" * 65)

    try:
        print("\n[IDLE] Waiting for wake word ('Alexa')...")
        while not is_wake_word_triggered:
            time.sleep(0.05)

        # 1. Wake word triggered
        detector.stop_listening()
        print("\n>>> [WAKE WORD DETECTED!]")
        tts.speak("Yes?")

        # 2. Record command with VAD
        print("[LISTENING] Speak now...")
        command_audio = recorder.record_phrase(
            mic,
            on_speech_start=lambda: print("  [*] Voice activity detected! [Speaking] ", end="", flush=True),
            on_speech_chunk=lambda energy: print(".", end="", flush=True),
        )
        print()

        # 3. Transcribe audio to text
        print("[+] Transcribing speech...")
        t0 = time.time()
        user_text = stt.transcribe(command_audio)
        stt_latency = time.time() - t0
        print(f"  >>> [USER SAID]: \"{user_text}\" ({stt_latency:.2f}s)")

        if not user_text:
            tts.speak("I could not hear anything.")
            return

        # 4. LLM processes intent & response
        print(f"[+] Thinking with LLM ({config.llm.model})...")
        t1 = time.time()
        intent = agent.process_command(user_text)
        llm_latency = time.time() - t1

        print(f"  >>> [ACTION]:    {intent.action}")
        print(f"  >>> [TARGET]:    {intent.target}")
        print(f"  >>> [LLM REPLY]: \"{intent.speech_reply}\" ({llm_latency:.2f}s)")

        # 5. Speak reply with Piper neural voice
        print(f"[+] Speaking response...")
        tts.speak(intent.speech_reply)

        print("\n[SUCCESS] Complete pipeline loop finished!")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\n[+] Exiting...")
    finally:
        detector.stop_listening()
        mic.stop()

if __name__ == "__main__":
    main()
