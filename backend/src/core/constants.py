"""Central constants for Desktop Handsfree Assistant backend."""

# ---------------------------------------------------------------------------
# Wake Word Constants
# ---------------------------------------------------------------------------
# Default active wake word(s)
DEFAULT_WAKEWORD_MODELS = ["alexa"]

# Detection confidence threshold (0.0 to 1.0)
DEFAULT_WAKEWORD_THRESHOLD = 0.5

# List of pre-trained models available offline in openWakeWord
AVAILABLE_WAKEWORD_MODELS = [
    "alexa",
    "hey_jarvis",
    "hey_mycroft",
    "hey_rhasspy",
    "timer",
    "weather",
]

# ---------------------------------------------------------------------------
# Audio Hardware Constants
# ---------------------------------------------------------------------------
# Standard sample rate in Hz (openWakeWord and Whisper expect 16kHz)
AUDIO_SAMPLE_RATE = 16000

# Single channel (mono) is standard for speech processing
AUDIO_CHANNELS = 1

# 1280 samples at 16kHz = 80ms chunk size (openWakeWord's native frame window)
AUDIO_CHUNK_SIZE = 1280

# ---------------------------------------------------------------------------
# Voice Activity Detection (VAD) & Recorder Constants
# ---------------------------------------------------------------------------
# Energy threshold for speech detection (16-bit PCM RMS value)
# Typical ambient room: 100-300; Speaking: 1000-8000
DEFAULT_VAD_ENERGY_THRESHOLD = 500

# Seconds of silence after speech before considering the command finished
DEFAULT_VAD_SILENCE_TIMEOUT = 1.6

# Seconds to wait for user to start speaking after wake word activation
DEFAULT_VAD_INITIAL_TIMEOUT = 4.0

# Maximum duration (in seconds) to record a single command as a safety cutoff
DEFAULT_VAD_MAX_RECORD_TIME = 10.0

# ---------------------------------------------------------------------------
# Speech-to-Text (STT) Constants (Faster-Whisper)
# ---------------------------------------------------------------------------
# Whisper model size: 'base' (multilingual, supports Hindi & English seamlessly)
DEFAULT_STT_MODEL_SIZE = "base"

# Hardware execution device: 'cpu' (or 'cuda' if Nvidia GPU is present)
DEFAULT_STT_DEVICE = "cpu"

# Quantization type: 'int8' gives blazing fast speed and low RAM usage on CPU
DEFAULT_STT_COMPUTE_TYPE = "int8"

# Spoken language: 'auto' automatically detects Hindi vs English
DEFAULT_STT_LANGUAGE = "auto"

# ---------------------------------------------------------------------------
# Text-to-Speech (TTS) Constants (Offline Neural Piper)
# ---------------------------------------------------------------------------
# Natural neural voice model name
DEFAULT_TTS_VOICE = "en_US-lessac-medium"

# Speaking speed multiplier (1.0 = normal, 1.15 = natural conversational pace)
DEFAULT_TTS_SPEED = 1.15

# ---------------------------------------------------------------------------
# LLM & Intent Engine Constants (OpenAI SDK Compatible)
# ---------------------------------------------------------------------------
# Base URL for any OpenAI-compatible provider (e.g. Ollama, OpenRouter, LM Studio)
DEFAULT_LLM_BASE_URL = "http://localhost:11434/v1"

# Target LLM model name
DEFAULT_LLM_MODEL = "llama3.2"

# API key placeholder (not needed for local Ollama)
DEFAULT_LLM_API_KEY = "ollama"

# Sampling temperature (low temperature = deterministic intent extraction)
DEFAULT_LLM_TEMPERATURE = 0.2

# ---------------------------------------------------------------------------
# Application Constants
# ---------------------------------------------------------------------------
DEFAULT_APP_ENV = "development"
DEFAULT_DEBUG = True
