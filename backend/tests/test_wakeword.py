"""Interactive integration test for AudioCapture and WakeWordDetector."""

import sys
import time
from pathlib import Path

# Ensure backend directory is on sys.path so 'src' imports resolve cleanly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.audio.capture import AudioCapture
from src.wakeword.detector import WakeWordDetector
from src.core.config import config

def on_wake_word(model_name: str, confidence: float) -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"\n[{timestamp}] >>> [WAKE WORD DETECTED!] Target: '{model_name}' (Confidence: {confidence:.2f})")

def main() -> None:
    print("=" * 65)
    print("  Desktop Handsfree Assistant - Scalable Wake Word Test")
    print("=" * 65)

    # 1. Enumerate available input devices
    devices = AudioCapture.list_input_devices()
    print(f"[+] Found {len(devices)} audio input device(s):")
    for dev in devices:
        print(f"    - [{dev['index']}] {dev['name']} ({dev['channels']} ch, {dev['sample_rate']} Hz)")

    # 2. Initialize hardware capture abstraction
    print(f"\n[+] Initializing AudioCapture (SampleRate={config.audio.sample_rate}Hz)...")
    mic = AudioCapture()

    # 3. Initialize wake word engine
    print(f"[+] Initializing WakeWordDetector (Models={config.wakeword.models}, Threshold={config.wakeword.threshold})...")
    detector = WakeWordDetector(on_detection=on_wake_word)

    # 4. Attach detector to microphone stream
    detector.start_listening(mic)

    print("=" * 65)
    print("  * MICROPHONE & WAKE WORD ENGINE ACTIVE *")
    prompt_words = " or ".join(f"'{Path(m).stem.split('_v0')[0]}'" for m in config.wakeword.models)
    print(f"  Speak into your microphone and say: {prompt_words}")
    print("  (Press Ctrl+C to stop)")
    print("=" * 65)

    mic.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[+] Interrupt received. Shutting down gracefully...")
    finally:
        detector.stop_listening()
        mic.stop()
        print("[+] AudioCapture stopped and stream released. Test finished.")

if __name__ == "__main__":
    main()
