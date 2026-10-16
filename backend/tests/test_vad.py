"""Integration test: Wake Word ('Alexa') triggers VAD to record a user speech command."""

import sys
import time
import wave
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.audio.capture import AudioCapture
from src.audio.recorder import AudioRecorder
from src.wakeword.detector import WakeWordDetector
from src.core.config import config

def save_wav(filename: Path, audio_data, sample_rate: int = 16000) -> None:
    """Save captured 16-bit PCM audio samples to a standard .wav file."""
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 2 bytes = 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Wake Word + VAD Recorder Test")
    print("=" * 65)

    mic = AudioCapture()
    detector = WakeWordDetector()
    recorder = AudioRecorder()

    is_wake_word_triggered = False

    def on_wake(model_name: str, confidence: float) -> None:
        nonlocal is_wake_word_triggered
        is_wake_word_triggered = True

    detector.on_detection = on_wake
    detector.start_listening(mic)
    mic.start()

    print("\n[+] System is active.")
    print("  1. Say: 'Alexa'")
    print("  2. Speak your command (e.g. 'Open my browser and search for weather')")
    print("  3. Stop talking and pause for 1 second")
    print("=" * 65)

    try:
        while True:
            # Step 1: Wait for wake word
            print("\n[IDLE] Waiting for wake word ('Alexa')...")
            while not is_wake_word_triggered:
                time.sleep(0.05)

            # Step 2: Wake word triggered! Pause wake word detector so it doesn't interfere
            detector.stop_listening()
            print("\n>>> [WAKE WORD DETECTED!]")
            print("[LISTENING] Speak your command now...")

            # Step 3: Record the command with VAD
            command_audio = recorder.record_phrase(
                mic,
                on_speech_start=lambda: print("  [*] Voice activity detected! [Speaking] ", end="", flush=True),
                on_speech_chunk=lambda energy: print(".", end="", flush=True),
            )
            print()

            duration = len(command_audio) / config.audio.sample_rate
            print(f"[SUCCESS] Command captured! Duration: {duration:.2f} seconds ({len(command_audio)} samples).")

            # Save to wav so user can verify audio quality
            wav_path = Path(__file__).parent / "captured_command.wav"
            save_wav(wav_path, command_audio, sample_rate=config.audio.sample_rate)
            print(f"[+] Saved recording to: {wav_path.resolve()}")

            print("\n[TEST COMPLETED SUCCESSFULLY]")
            break

    except KeyboardInterrupt:
        print("\n[+] Interrupted by user.")
    finally:
        detector.stop_listening()
        mic.stop()
        print("[+] AudioCapture released. Clean exit.")

if __name__ == "__main__":
    main()
