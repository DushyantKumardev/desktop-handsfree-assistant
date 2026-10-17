"""Interactive test for local Speech-to-Text transcription with Faster-Whisper."""

import sys
import time
import wave
from pathlib import Path
import numpy as np

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.audio.capture import AudioCapture
from src.audio.recorder import AudioRecorder
from src.wakeword.detector import WakeWordDetector
from src.stt.transcriber import STTTranscriber
from src.core.config import config

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Local Speech-to-Text (STT)")
    print("=" * 65)

    # 1. Initialize STT engine
    print(f"[+] Loading Faster-Whisper ({config.stt.model_size} on {config.stt.device})...")
    stt = STTTranscriber()

    # 2. Check if a previously recorded audio file exists for quick verification
    wav_path = Path(__file__).parent / "captured_command.wav"
    if wav_path.exists():
        print(f"\n[+] Found existing audio file: {wav_path.name}")
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            prev_audio = np.frombuffer(frames, dtype=np.int16)

        t0 = time.time()
        prev_text = stt.transcribe(prev_audio)
        elapsed = time.time() - t0
        print(f"    Previous recording transcription: '{prev_text}' ({elapsed:.2f}s)")

    # 3. Live end-to-end test: Mic -> Wake Word -> VAD -> STT
    print("\n" + "=" * 65)
    print("  * LIVE VOICE RECOGNITION TEST *")
    print("  1. Say: 'Alexa'")
    print("  2. Speak your command (e.g. 'Open YouTube and search for Python')")
    print("  3. Stop talking and wait for the transcription")
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

    try:
        print("\n[IDLE] Waiting for wake word ('Alexa')...")
        while not is_wake_word_triggered:
            time.sleep(0.05)

        detector.stop_listening()
        print("\n>>> [WAKE WORD DETECTED!]")
        print("[LISTENING] Speak your command now...")

        # Record speech with VAD
        command_audio = recorder.record_phrase(
            mic,
            on_speech_start=lambda: print("  [*] Voice activity detected! [Speaking] ", end="", flush=True),
            on_speech_chunk=lambda energy: print(".", end="", flush=True),
        )
        print()

        duration = len(command_audio) / config.audio.sample_rate
        print(f"[+] Audio recorded: {duration:.2f}s ({len(command_audio)} samples)")

        # Transcribe locally with Faster-Whisper
        print("[+] Transcribing locally with Faster-Whisper...")
        t0 = time.time()
        text = stt.transcribe(command_audio)
        latency = time.time() - t0

        print("=" * 65)
        print(f"  >>> [TRANSCRIBED COMMAND]: \"{text}\"")
        print(f"  >>> [INFERENCE LATENCY]:  {latency:.2f} seconds")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\n[+] Test stopped by user.")
    finally:
        detector.stop_listening()
        mic.stop()
        print("[+] AudioCapture stopped. Clean exit.")

if __name__ == "__main__":
    main()
