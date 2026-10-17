# Backend Voice & Automation Engine

This folder contains the core Python engine for the Desktop Handsfree Assistant.

## Architecture

```text
backend/
├── src/
│   ├── core/           # Central configuration, logging, and events
│   ├── audio/          # Hardware abstraction layer (microphone capture & speaker playback)
│   ├── wakeword/       # Wake word detection engine (openWakeWord ONNX models)
│   ├── stt/            # Speech-to-Text transcription (Future: Whisper)
│   ├── agent/          # Reasoning and command dispatching
│   ├── tts/            # Text-to-Speech synthesis
│   ├── automation/     # Desktop OS automation actions
│   └── api/            # Local IPC / WebSocket server for frontend
│
├── tests/              # Test suite and interactive verification scripts
├── requirements.txt    # Production & development dependencies
└── .venv/              # Isolated Python virtual environment
```

## Running Tests

From the `backend/` directory with the virtual environment activated:

```powershell
# Verify environment isolation and dependencies
python tests/test_env.py

# Live wake word test with microphone
python tests/test_wakeword.py

# Voice activity detection & command recording test
python tests/test_vad.py

# Full end-to-end Voice Recognition (Mic -> Wake Word -> VAD -> Local STT)
python tests/test_stt.py

# Offline Neural Text-to-Speech test (Piper)
python tests/test_tts.py
```
