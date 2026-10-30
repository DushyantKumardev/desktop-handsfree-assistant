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
from src.core.messages import AssistantResponses
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
        self._is_followup = False
        self._cancel_requested = threading.Event()
        self._active_speech_queue: Optional[queue.Queue[Optional[str]]] = None

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

        def handle_cancel() -> None:
            logger.info("[CANCEL] Stop requested by client.")
            self._cancel_requested.set()
            self._wake_triggered = False
            self._is_followup = False
            self.recorder.cancel()
            self.tts.stop()
            if self._active_speech_queue is not None:
                while not self._active_speech_queue.empty():
                    try:
                        self._active_speech_queue.get_nowait()
                        self._active_speech_queue.task_done()
                    except Exception:
                        break
                try:
                    self._active_speech_queue.put_nowait(None)
                except Exception:
                    pass
            self.brain.reset_conversation()
            ws_server.broadcast_state("idle")

        def handle_reset_session() -> None:
            logger.info("[SESSION] Reset requested: Clearing conversation memory for a completely new session.")
            self.brain.reset_conversation()
            self._is_followup = False
            self._wake_triggered = False
            self._cancel_requested.set()
            self.recorder.cancel()
            self.tts.stop()
            if self._active_speech_queue is not None:
                while not self._active_speech_queue.empty():
                    try:
                        self._active_speech_queue.get_nowait()
                        self._active_speech_queue.task_done()
                    except Exception:
                        break
                try:
                    self._active_speech_queue.put_nowait(None)
                except Exception:
                    pass
            ws_server.broadcast_state("idle")

        ws_server.on_cancel_requested = handle_cancel
        ws_server.on_reset_session = handle_reset_session
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
            self._is_followup = False
            while self.running:
                if not self._wake_triggered:
                    time.sleep(0.02)
                    continue

                # 1. Reset cancellation state & TTS stop flag for this new turn
                self._cancel_requested.clear()
                self.tts.reset()

                # 2. Immediately pause wake word detection to prevent false triggers during command/speech
                self.detector.stop_listening()
                self._wake_triggered = False
                is_followup = self._is_followup
                self._is_followup = False

                if is_followup:
                    print("\n>>> [FOLLOW-UP LISTENING CYCLE ACTIVATED]")
                    ws_server.broadcast_show_widget()
                    ws_server.broadcast_state("listening", is_followup=True)
                else:
                    print("\n>>> [WAKE WORD DETECTED!]")
                    ws_server.broadcast_show_widget()
                    ws_server.broadcast_state("listening", is_followup=False)

                # 3. Play listening sound cue and flush microphone buffer
                self.sounds.play_start()
                self.mic.flush_queue()

                # 4. Record voice command using Voice Activity Detection
                print("[LISTENING] Listening for your command...", flush=True)
                command_audio = self.recorder.record_phrase(self.mic)

                if self._cancel_requested.is_set():
                    print("[CANCEL] Aborted during voice recording.\n")
                    self._reset_and_listen()
                    continue

                self.sounds.play_stop(wait=False)

                # 5. Transcribe speech using Whisper
                print("[+] Processing STT...", flush=True)
                ws_server.broadcast_state("thinking")
                t_stt = time.time()
                user_text = self.stt.transcribe(command_audio)
                stt_latency = time.time() - t_stt

                if self._cancel_requested.is_set():
                    print("[CANCEL] Aborted during transcription.\n")
                    self._reset_and_listen()
                    continue

                if not user_text:
                    if is_followup:
                        print("[FOLLOW-UP] No speech heard for follow-up question. Ending turn.\n")
                        is_followup = False
                        ws_server.broadcast_state("idle")
                        self._reset_and_listen()
                        continue
                    if self._cancel_requested.is_set():
                        self._reset_and_listen()
                        continue
                    self.tts.speak(AssistantResponses.NO_SPEECH_HEARD)
                    ws_server.broadcast_state("idle")
                    self._reset_and_listen()
                    continue

                turn_label = " (FOLLOW-UP)" if is_followup else ""
                print(f">>> [USER{turn_label}]: \"{user_text}\" ({stt_latency:.2f}s)")
                ws_server.broadcast_transcription(user_text)

                # Reset follow-up status for current processing turn
                is_followup = False

                # 6. LLM Brain with Live Token Streaming & Tool Collection
                t_llm = time.time()
                first_speech = True

                # Background speech worker queue so all sentences stream seamlessly in order
                speech_queue: queue.Queue[Optional[str]] = queue.Queue()
                self._active_speech_queue = speech_queue

                def speech_worker() -> None:
                    while True:
                        if self._cancel_requested.is_set():
                            break
                        try:
                            item = speech_queue.get(timeout=0.1)
                        except queue.Empty:
                            continue
                        if item is None:
                            speech_queue.task_done()
                            break
                        try:
                            if not self._cancel_requested.is_set():
                                self.tts.speak(item, stream=True)
                        except Exception as e:
                            logger.error("TTS playback error: %s", e)
                        finally:
                            speech_queue.task_done()

                tts_thread = threading.Thread(target=speech_worker, daemon=True)
                tts_thread.start()

                def on_sentence(sentence: str) -> None:
                    nonlocal first_speech
                    if self._cancel_requested.is_set():
                        return
                    cleaned = TTSSynthesizer.clean_spoken_text(sentence)
                    if not cleaned or self._cancel_requested.is_set():
                        return
                    # Broadcast each sentence chunk to frontend in real time
                    ws_server.broadcast_state("speaking")
                    ws_server.broadcast_stream_chunk(cleaned, user_text)

                    if first_speech:
                        first_speech = False
                    speech_queue.put(cleaned)

                llm_resp = self.brain.process_command(
                    user_text,
                    on_sentence_ready=on_sentence,
                    is_cancelled=self._cancel_requested.is_set,
                )
                llm_latency = time.time() - t_llm

                if self._cancel_requested.is_set():
                    print("[CANCEL] Aborted during LLM streaming.\n")
                    self.tts.stop()
                    self._drain_queue(speech_queue)
                    tts_thread.join(timeout=0.5)
                    self._active_speech_queue = None
                    self._reset_and_listen()
                    continue

                clean_reply = TTSSynthesizer.clean_spoken_text(llm_resp.spoken_reply)
                if clean_reply:
                    print(f">>> [ASSISTANT]: \"{clean_reply}\" ({llm_latency:.2f}s)")

                # 7. Native Tool Execution
                if llm_resp.tool_calls:
                    if self._cancel_requested.is_set():
                        self.tts.stop()
                        self._drain_queue(speech_queue)
                        tts_thread.join(timeout=0.5)
                        self._active_speech_queue = None
                        self._reset_and_listen()
                        continue

                    for tc in llm_resp.tool_calls:
                        print(f">>> [ACTION]: {tc.name}({tc.args})")

                    exec_results = self.executor.execute_tools(llm_resp.tool_calls)
                    for tc, res in zip(llm_resp.tool_calls, exec_results):
                        if self._cancel_requested.is_set():
                            break
                        # Information tools (get_schedules, web_search): return findings to LLM so AI answers in its own words!
                        if tc.name in ("get_schedules", "web_search"):
                            findings = ""
                            if res.data and isinstance(res.data, dict):
                                findings = res.data.get("summary") or res.data.get("snippets") or ""
                            elif res.message:
                                findings = res.message
                            elif res.spoken_override:
                                findings = res.spoken_override

                            if findings:
                                from src.core.events import emit_status
                                emit_status("Just a sec...")
                                print(f"[*] Synthesizing {tc.name} findings with LLM...")
                                synth_text = self.brain.synthesize_tool_answer(
                                    user_query=user_text,
                                    tool_name=tc.name,
                                    tool_data=findings,
                                    on_sentence_ready=on_sentence,
                                    is_cancelled=self._cancel_requested.is_set,
                                )
                                print(f">>> [AI ANSWER]: \"{synth_text}\"")
                                clean_reply = synth_text
                            else:
                                no_res_msg = "Couldn't find any information on that."
                                print(f">>> [AI ANSWER]: \"{no_res_msg}\"")
                                ws_server.broadcast_stream_chunk(no_res_msg, user_text)
                                speech_queue.put(no_res_msg)
                                clean_reply = no_res_msg
                        elif res.spoken_override and res.action == "set_speaking_speed":
                            # Only set_speaking_speed uses spoken_override for immediate rate demonstration
                            clean_override = TTSSynthesizer.clean_spoken_text(res.spoken_override)
                            ws_server.broadcast_stream_chunk(clean_override, user_text)
                            speech_queue.put(clean_override)
                            clean_reply = clean_override
                elif first_speech and clean_reply:
                    speech_queue.put(clean_reply)

                # Signal speech queue to finish and wait for all playback to complete
                speech_queue.put(None)
                tts_thread.join(timeout=10.0 if not self._cancel_requested.is_set() else 0.5)
                self._active_speech_queue = None

                if self._cancel_requested.is_set():
                    print("[CANCEL] Turn aborted before response completion.\n")
                    self._reset_and_listen()
                    continue

                # Signal completion to frontend
                ws_server.broadcast_response_complete(
                    user_text,
                    clean_reply or AssistantResponses.ACTION_COMPLETED,
                    needs_followup=llm_resp.needs_followup,
                )

                if llm_resp.needs_followup:
                    print(">>> [AI REQUESTED FOLLOW-UP (<followup/> detected)]")
                    time.sleep(0.35)
                    self.mic.flush_queue()
                    self._is_followup = True
                    self._wake_triggered = True
                else:
                    self._reset_and_listen()

        except KeyboardInterrupt:
            print("\n[*] Stopping assistant...")
        finally:
            self.stop()

    def _drain_queue(self, q: queue.Queue) -> None:
        """Safely empties a queue to prevent leftover items from being processed."""
        while not q.empty():
            try:
                q.get_nowait()
                q.task_done()
            except Exception:
                break
        try:
            q.put_nowait(None)
        except Exception:
            pass

    def _reset_and_listen(self) -> None:
        """Flushes buffers and resumes wake-word listening."""
        time.sleep(0.3)
        self.mic.flush_queue()
        self.detector.reset()
        self._wake_triggered = False
        self._is_followup = False
        self._cancel_requested.clear()
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
