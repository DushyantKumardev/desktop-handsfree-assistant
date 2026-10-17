"""Full end-to-end voice loop test: Mic -> WakeWord -> VAD -> STT -> TTS Echo."""

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
from src.tts.synthesizer import TTSSynthesizer
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Full Voice Loop Test")
    print("  (Mic -> Alexa -> VAD Record -> Faster-Whisper -> Piper TTS Echo)")
    print("=" * 65)

    print("[+] Initializing components...")
    mic = AudioCapture()
    detector = WakeWordDetector()
    recorder = AudioRecorder()
    stt = STTTranscriber()
    tts = TTSSynthesizer()

    is_wake_word_triggered = False

    def on_wake(model_name: str, confidence: float) -> None:
        nonlocal is_wake_word_triggered
        is_wake_word_triggered = True

    detector.on_detection = on_wake
    detector.start_listening(mic)
    mic.start()

    print("\n" + "=" * 65)
    print("  * SYSTEM READY *")
    print("  1. Say: 'Alexa'")
    print("  2. Speak your command (English or Hindi)")
    print("  3. Assistant will transcribe and repeat back what you said!")
    print("=" * 65)

    try:
        print("\n[IDLE] Listening for wake word ('Alexa')...")
        while not is_wake_word_triggered:
            time.sleep(0.05)

        # 1. Wake word detected: pause detector and acknowledge
        detector.stop_listening()
        print("\n>>> [WAKE WORD DETECTED!]")

        # Acknowledge with voice
        tts.speak("Yes?")

        # 2. Record command with VAD
        print("[LISTENING] Speak now...")
        command_audio = recorder.record_phrase(
            mic,
            on_speech_start=lambda: print("  [*] Voice activity detected! [Speaking] ", end="", flush=True),
            on_speech_chunk=lambda energy: print(".", end="", flush=True),
        )
        print()

        # 3. Transcribe with Whisper
        print("[+] Transcribing locally...")
        t0 = time.time()
        text = stt.transcribe(command_audio)
        stt_latency = time.time() - t0

        print(f"  >>> [TRANSCRIBED]: \"{text}\" ({stt_latency:.2f}s)")

        # 4. Echo back with Piper TTS
        if text:
            is_hindi = tts.detect_language(text) == "hi"
            reply_text = f"आपने कहा: {text}" if is_hindi else f"You said: {text}"
            print(f"  >>> [TTS SPEAKING]: \"{reply_text}\"")
            tts.speak(reply_text)
        else:
            tts.speak("I could not hear anything.")

        print("\n[SUCCESS] Full voice cycle completed!")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\n[+] Exiting...")
    finally:
        detector.stop_listening()
        mic.stop()

if __name__ == "__main__":
    main()
