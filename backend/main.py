"""
Desktop Handsfree Assistant - Main Entrypoint
Full continuous voice pipeline:
Wake Word -> Sound Cue -> VAD Speech Record -> Whisper STT -> LLM Brain (Streaming) -> Native Tool Execution -> Piper TTS (Streaming)
"""

import logging
import signal
import sys
import threading
import time
from typing import Optional
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.core.config import config
from src.audio.capture import AudioCapture
from src.audio.recorder import AudioRecorder
from src.audio.feedback import SoundFeedback
from src.wakeword.detector import WakeWordDetector
from src.stt.transcriber import STTTranscriber
from src.agent.brain import LLMBrain
from src.automation.executor import ActionExecutor
from src.tts.synthesizer import TTSSynthesizer

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Silence verbose third-party HTTP & audio debug logs
for noisy_lib in ("httpcore", "httpcore2", "httpx", "openai", "urllib3", "piper"):
    logging.getLogger(noisy_lib).setLevel(logging.WARNING)

logger = logging.getLogger("main")


class HandsfreeAssistant:
    """The master hands-free voice assistant daemon."""

    def __init__(self) -> None:
        self.running = False
        self._wake_triggered = False

        print("=" * 65)
        print("  Desktop Handsfree Voice Assistant (Offline First)")
        print(f"  Wake Word:  {config.wakeword.models}")
        print(f"  Whisper STT:{config.stt.model_size} ({config.stt.compute_type} on {config.stt.device})")
        print(f"  LLM Brain:  {config.llm.model} @ {config.llm.base_url}")
        print(f"  Piper TTS:  {config.tts.voice} (Streaming Playback)")
        print("=" * 65)
        print("\n[*] Initializing hardware & neural models...")

        t0 = time.time()
        self.mic = AudioCapture(config.audio)
        self.detector = WakeWordDetector(config.wakeword)
        self.recorder = AudioRecorder(config.vad)
        self.sounds = SoundFeedback(sound_config=config.sound)
        self.stt = STTTranscriber(config.stt)
        self.brain = LLMBrain(config.llm)
        self.executor = ActionExecutor()
        self.tts = TTSSynthesizer(config.tts)
        print(f"[+] All engines initialized in {time.time() - t0:.2f}s!\n")

    def _on_wake_detected(self, model_name: str, confidence: float) -> None:
        """Callback fired when wake word is detected."""
        self._wake_triggered = True

    def start(self) -> None:
        """Starts the assistant event loop."""
        self.running = True

        # Setup wake word callback and start audio capture
        self.detector.on_detection = self._on_wake_detected
        self.detector.start_listening(self.mic)
        self.mic.start()

        # Print banner
        wake_display = Path(config.wakeword.models[0]).stem.replace("_v0.1", "").capitalize()
        print("=" * 65)
        print("  * ASSISTANT IS LIVE AND LISTENING *")
        print(f"  1. Say: '{wake_display}'")
        print("  2. Wait for the chime, then speak your command naturally.")
        print("  (Press Ctrl+C to stop)")
        print("=" * 65 + "\n")

        try:
            while self.running:
                if not self._wake_triggered:
                    time.sleep(0.02)
                    continue

                # 1. Immediately pause wake word detection to prevent false triggers during command/speech
                self.detector.stop_listening()
                self._wake_triggered = False
                print("\n>>> [WAKE WORD DETECTED!]")

                # 2. Play listening sound cue and flush microphone buffer
                self.sounds.play_start()
                self.mic.flush_queue()

                # 3. Record voice command using Voice Activity Detection
                print("[LISTENING] Speak your command... ", end="", flush=True)
                command_audio = self.recorder.record_phrase(
                    self.mic,
                    on_speech_start=lambda: print("[Speaking] ", end="", flush=True),
                    on_speech_chunk=lambda energy: print(".", end="", flush=True),
                )
                print()
                self.sounds.play_stop(wait=False)

                # 4. Transcribe speech using Whisper
                print("[+] Transcribing speech...")
                t_stt = time.time()
                user_text = self.stt.transcribe(command_audio)
                stt_latency = time.time() - t_stt
                print(f"  >>> [USER]: \"{user_text}\" ({stt_latency:.2f}s)")

                if not user_text:
                    self.tts.speak("I could not hear anything.")
                    time.sleep(0.4)
                    self.mic.flush_queue()
                    self.detector.reset()
                    self._wake_triggered = False
                    self.detector.start_listening(self.mic)
                    print("[IDLE] Waiting for wake word...\n")
                    continue

                # 5. LLM Brain with Live Token Streaming & Tool Collection
                print(f"[+] Thinking with LLM ({config.llm.model}): ", end="", flush=True)
                t_llm = time.time()
                early_spoken = False
                tts_thread: Optional[threading.Thread] = None

                def on_reply_ready(early_reply: str) -> None:
                    nonlocal early_spoken, tts_thread
                    # If user is asking for clock time, let the executor provide exact ground truth
                    if any(w in user_text.lower() for w in ("time", "samay", "baj", "waqt", "date", "tarikh")):
                        return
                    if not early_spoken and early_reply:
                        early_spoken = True
                        ttfa = time.time() - t_llm
                        print(f"\n[+] [TTS STREAMING] Started speech in {ttfa:.2f}s: \"{early_reply}\"")
                        # Play speech asynchronously in parallel with tool preparation
                        tts_thread = threading.Thread(
                            target=self.tts.speak,
                            args=(early_reply,),
                            kwargs={"stream": True},
                            daemon=True,
                        )
                        tts_thread.start()

                llm_resp = self.brain.process_command(
                    user_text,
                    on_reply_ready=on_reply_ready,
                    on_token=lambda tok: print(tok, end="", flush=True),
                )
                print()  # Newline after token stream
                llm_latency = time.time() - t_llm
                print(f"  >>> [LLM REPLY]: \"{llm_resp.spoken_reply}\" ({llm_latency:.2f}s)")

                # 6. Native Tool Execution
                if llm_resp.tool_calls:
                    for tc in llm_resp.tool_calls:
                        print(f"  >>> [TOOL CALL]: {tc.name}({tc.args})")
                    exec_results = self.executor.execute_tools(llm_resp.tool_calls)
                    for res in exec_results:
                        print(f"  >>> [EXECUTION]: {res.message} (Success: {res.success})")
                        if res.spoken_override:
                            if tts_thread and tts_thread.is_alive():
                                tts_thread.join()
                            print(f"[+] Speaking ground truth: \"{res.spoken_override}\"")
                            self.tts.speak(res.spoken_override)
                elif not early_spoken:
                    # Direct conversation without tools
                    print(f"[+] Speaking response: \"{llm_resp.spoken_reply}\"")
                    self.tts.speak(llm_resp.spoken_reply)

                # Wait for any active speech playback to complete before reopening the microphone
                if tts_thread and tts_thread.is_alive():
                    tts_thread.join()

                # Echo cooldown & mic queue flush to prevent audio feedback
                time.sleep(0.5)
                self.mic.flush_queue()
                self.detector.reset()
                self._wake_triggered = False

                # Resume wake word detection with fresh microphone stream
                self.detector.start_listening(self.mic)

                print("[SUCCESS] Command finished! Ready for next wake word.")
                print("[IDLE] Waiting for wake word...\n")

        except KeyboardInterrupt:
            print("\n[*] Stopping assistant...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Clean shutdown and resource deallocation."""
        self.running = False
        try:
            self.detector.stop_listening()
            self.mic.stop()
        except Exception:
            pass
        print("[+] Assistant stopped successfully.")


def main() -> None:
    assistant = HandsfreeAssistant()

    # Graceful termination handlers
    def handle_signal(sig, frame):
        assistant.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    assistant.start()


if __name__ == "__main__":
    main()
