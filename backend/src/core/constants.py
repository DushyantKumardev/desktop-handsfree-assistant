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
# Application Constants
# ---------------------------------------------------------------------------
DEFAULT_APP_ENV = "development"
DEFAULT_DEBUG = True
