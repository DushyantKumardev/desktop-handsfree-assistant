"""
Handsfree Assistant Engine: Manages the complete voice interaction pipeline.
Pipeline: Wake Word -> Sound Cue -> VAD Speech Record -> Whisper STT -> LLM Brain (Streaming) -> Native Tool Execution -> Piper TTS (Streaming)
"""

import logging
import queue
import random
import re
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

from src.core.config import config
from src.audio.capture import AudioCapture
from src.audio.recorder import AudioRecorder
from src.audio.feedback import SoundFeedback
from src.wakeword.detector import WakeWordDetector
from src.stt.transcriber import STTTranscriber
from src.agent.brain import LLMBrain
from src.automation.executor import ActionExecutor
from src.tts.synthesizer import TTSSynthesizer
from src.server.ws_server import ws_server

logger = logging.getLogger("assistant")


class HandsfreeAssistant:
    """The master hands-free voice assistant daemon."""

    def __init__(self) -> None:
        self.running = False
        self._wake_triggered = False

        t0 = time.time()
        self.mic = AudioCapture(config.audio)
        self.detector = WakeWordDetector(config.wakeword)
        self.recorder = AudioRecorder(config.vad)
        self.sounds = SoundFeedback(sound_config=config.sound)
        self.stt = STTTranscriber(config.stt)
        self.brain = LLMBrain(config.llm)
        self.executor = ActionExecutor()
        self.tts = TTSSynthesizer(config.tts)

        # Connect WebSocket broadcast server for frontend overlay
        ws_server.on_trigger_listen = lambda: setattr(self, "_wake_triggered", True)
        def handle_cancel():
            self._wake_triggered = False
            self.brain.reset_conversation()
            self._reset_and_listen()
        ws_server.on_cancel_requested = handle_cancel
        ws_server.start()

        self._print_banner()
        print(f"[+] All engines initialized in {time.time() - t0:.2f}s!\n")

    def _print_banner(self) -> None:
        """Displays system configuration overview."""
        print("=" * 65)
        print("  Desktop Handsfree Voice Assistant (Offline First)")
        print(f"  Wake Word:  {config.wakeword.models}")
        print(f"  Whisper STT:{config.stt.model_size} ({config.stt.compute_type} on {config.stt.device})")
        print(f"  LLM Brain:  {config.llm.model} @ {config.llm.base_url}")
        print(f"  Piper TTS:  {config.tts.voice} (Speed: {self.tts.speed:.2f}x)")
        print("=" * 65)

    @staticmethod
    def _get_tool_engagement_phrase(tool_call: Any, user_text: str) -> str:
        """Dynamic conversational engagement spoken before executing long-running tools."""
        name = getattr(tool_call, "name", "")
        args = getattr(tool_call, "args", {}) or {}
        query = args.get("query", "").strip()
        is_hindi = any(w in user_text.lower() for w in ("kya", "kaun", "kab", "kaha", "batao", "dhundo", "khojo", "karo", "hai", "mujhe", "samay", "baj"))

        if name == "web_search":
            if is_hindi:
                options = [
                    "Main abhi internet par check karke batata hoon, ek second.",
                    "Dekhta hoon, online search kar raha hoon, ek pal dijiye.",
                    "Iske baare mein abhi search karta hoon, bas ek second.",
                ]
            else:
                if query:
                    clean_q = re.sub(r"[^\w\s]", "", query)
                    options = [
                        f"Let me check the web for {clean_q}, give me just a moment.",
                        f"Looking that up on the web for you right now, one second.",
                        f"Searching online for {clean_q}, give me a second.",
                        f"Let me find that information for you, one moment.",
                    ]
                else:
                    options = [
                        "Let me check the web for that, give me just a moment.",
                        "Looking into that right now, one moment.",
                        "Searching online for you, give me a second.",
                    ]
            return random.choice(options)

        elif name == "play_media":
            if is_hindi:
                return f"YouTube par {query} dhoondh raha hoon, ek second." if query else "YouTube chala raha hoon, ek second."
            return f"Looking up {query} on YouTube for you, one moment." if query else "Opening YouTube for you, one moment."

        elif name == "open_app":
            app = args.get("app_name", "app")
            return f"{app} open kar raha hoon, ek second." if is_hindi else f"Opening {app} for you right away."

        elif name == "get_time_date":
            return "Samay check karta hoon, ek second." if is_hindi else "Checking the time for you, one moment."

        elif name == "set_speaking_speed":
            # set_speaking_speed provides its own immediate spoken confirmation at the new speed
            return ""

        return "Working on that for you, give me a moment."

    def _on_wake_detected(self, model_name: str, confidence: float) -> None:
        """Callback fired when wake word is detected."""
        self._wake_triggered = True
        ws_server.broadcast_show_widget()
        ws_server.broadcast_state("listening")

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
        print("[IDLE] Waiting for wake word...\n")

        try:
            is_followup = False
            while self.running:
                if not self._wake_triggered:
                    time.sleep(0.02)
                    continue

                # 1. Immediately pause wake word detection to prevent false triggers during command/speech
                self.detector.stop_listening()
                self._wake_triggered = False

                if is_followup:
                    print("\n>>> [FOLLOW-UP LISTENING CYCLE ACTIVATED]")
                    ws_server.broadcast_show_widget()
                    ws_server.broadcast_state("listening", is_followup=True)
                else:
                    print("\n>>> [WAKE WORD DETECTED!]")
                    ws_server.broadcast_show_widget()
                    ws_server.broadcast_state("listening", is_followup=False)

                # 2. Play listening sound cue and flush microphone buffer
                self.sounds.play_start()
                self.mic.flush_queue()

                # 3. Record voice command using Voice Activity Detection
                print("[LISTENING] Listening for your command...", flush=True)
                command_audio = self.recorder.record_phrase(self.mic)
                self.sounds.play_stop(wait=False)

                # 4. Transcribe speech using Whisper
                print("[+] Processing STT...", flush=True)
                ws_server.broadcast_state("thinking")
                t_stt = time.time()
                user_text = self.stt.transcribe(command_audio)
                stt_latency = time.time() - t_stt

                if not user_text:
                    if is_followup:
                        print("[FOLLOW-UP] No speech heard for follow-up question. Ending turn.\n")
                        is_followup = False
                        ws_server.broadcast_state("idle")
                        self._reset_and_listen()
                        continue
                    self.tts.speak("I could not hear anything.")
                    ws_server.broadcast_state("idle")
                    self._reset_and_listen()
                    continue

                turn_label = " (FOLLOW-UP)" if is_followup else ""
                print(f">>> [USER{turn_label}]: \"{user_text}\" ({stt_latency:.2f}s)")
                ws_server.broadcast_transcription(user_text)

                # Reset follow-up status for current processing turn
                is_followup = False

                # 5. LLM Brain with Live Token Streaming & Tool Collection
                t_llm = time.time()
                first_speech = True

                # Background speech worker queue so all sentences stream seamlessly in order
                speech_queue: queue.Queue[Optional[str]] = queue.Queue()

                def speech_worker() -> None:
                    while True:
                        item = speech_queue.get()
                        if item is None:
                            speech_queue.task_done()
                            break
                        try:
                            self.tts.speak(item, stream=True)
                        except Exception as e:
                            logger.error("TTS playback error: %s", e)
                        finally:
                            speech_queue.task_done()

                tts_thread = threading.Thread(target=speech_worker, daemon=True)
                tts_thread.start()

                def on_sentence(sentence: str) -> None:
                    nonlocal first_speech
                    cleaned = TTSSynthesizer.clean_spoken_text(sentence)
                    if not cleaned:
                        return
                    # Broadcast each sentence chunk to frontend in real time
                    ws_server.broadcast_state("speaking")
                    ws_server.broadcast_stream_chunk(cleaned, user_text)

                    # If user is asking for clock time, let the executor provide exact ground truth
                    if any(w in user_text.lower() for w in ("time", "samay", "baj", "waqt", "date", "tarikh")):
                        return
                    if first_speech:
                        first_speech = False
                    speech_queue.put(cleaned)

                llm_resp = self.brain.process_command(
                    user_text,
                    on_sentence_ready=on_sentence,
                )
                llm_latency = time.time() - t_llm
                clean_reply = TTSSynthesizer.clean_spoken_text(llm_resp.spoken_reply)
                if clean_reply:
                    print(f">>> [ASSISTANT]: \"{clean_reply}\" ({llm_latency:.2f}s)")

                # 6. Native Tool Execution
                if llm_resp.tool_calls:
                    for tc in llm_resp.tool_calls:
                        print(f">>> [ACTION]: {tc.name}({tc.args})")

                    # If the LLM didn't speak an opener, engage user with short talk before calling tool
                    if first_speech or not clean_reply:
                        engagement = self._get_tool_engagement_phrase(llm_resp.tool_calls[0], user_text)
                        if engagement:
                            first_speech = False
                            clean_eng = TTSSynthesizer.clean_spoken_text(engagement)
                            print(f">>> [ENGAGEMENT]: \"{clean_eng}\"")
                            ws_server.broadcast_stream_chunk(clean_eng, user_text)
                            speech_queue.put(clean_eng)

                    exec_results = self.executor.execute_tools(llm_resp.tool_calls)
                    for res in exec_results:
                        if res.spoken_override:
                            clean_override = TTSSynthesizer.clean_spoken_text(res.spoken_override)
                            print(f">>> [RESULT]: \"{clean_override}\"")
                            ws_server.broadcast_stream_chunk(clean_override, user_text)
                            speech_queue.put(clean_override)
                elif first_speech and clean_reply:
                    speech_queue.put(clean_reply)

                # Signal speech queue to finish and wait for all playback to complete
                speech_queue.put(None)
                tts_thread.join()

                # Signal completion to frontend
                ws_server.broadcast_response_complete(
                    user_text,
                    clean_reply or "Action completed.",
                    needs_followup=llm_resp.needs_followup,
                )

                if llm_resp.needs_followup:
                    print(">>> [AI REQUESTED FOLLOW-UP (<followup/> detected)]")
                    time.sleep(0.35)
                    self.mic.flush_queue()
                    is_followup = True
                    self._wake_triggered = True
                else:
                    self._reset_and_listen()

        except KeyboardInterrupt:
            print("\n[*] Stopping assistant...")
        finally:
            self.stop()

    def _reset_and_listen(self) -> None:
        """Flushes buffers and resumes wake-word listening."""
        time.sleep(0.4)
        self.mic.flush_queue()
        self.detector.reset()
        self._wake_triggered = False
        self.detector.start_listening(self.mic)
        print("[IDLE] Waiting for wake word...\n")

    def stop(self) -> None:
        """Clean shutdown and resource deallocation."""
        self.running = False
        try:
            self.detector.stop_listening()
            self.mic.stop()
        except Exception:
            pass
        print("[+] Assistant stopped successfully.")
