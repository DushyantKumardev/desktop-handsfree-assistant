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
# Whisper model size: 'tiny.en' (~75MB) or 'base.en' (~145MB, recommended)
DEFAULT_STT_MODEL_SIZE = "base.en"

# Hardware execution device: 'cpu' (or 'cuda' if Nvidia GPU is present)
DEFAULT_STT_DEVICE = "cpu"

# Quantization type: 'int8' gives blazing fast speed and low RAM usage on CPU
DEFAULT_STT_COMPUTE_TYPE = "int8"

# Spoken language
DEFAULT_STT_LANGUAGE = "en"

# ---------------------------------------------------------------------------
# Application Constants
# ---------------------------------------------------------------------------
DEFAULT_APP_ENV = "development"
DEFAULT_DEBUG = True
