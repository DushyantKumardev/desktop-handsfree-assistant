"""Audio feedback cues (start and stop earcons) supporting MP3, WAV, and custom audio formats."""

import logging
import wave
from pathlib import Path
from typing import Optional, Union
import numpy as np
import sounddevice as sd
from src.core.config import SoundConfig, config

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "sounds"


class SoundFeedback:
    """Plays sound effects for voice assistant interaction cues (start/stop listening)."""

    def __init__(
        self,
        sounds_dir: Optional[Union[Path, SoundConfig]] = None,
        sound_config: Optional[SoundConfig] = None,
    ) -> None:
        if isinstance(sounds_dir, SoundConfig):
            sound_config = sounds_dir
            sounds_dir = None

        self.sounds_dir = sounds_dir or ASSETS_DIR
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        self.config = sound_config or config.sound

        self.start_sound_path = self._resolve_sound_file(self.config.start_file, default_stem="start")
        self.stop_sound_path = self._resolve_sound_file(self.config.stop_file, default_stem="stop")

        # Generate pleasant default tones if no audio files exist
        self._ensure_default_sounds()

        # Cache audio arrays in memory for instant, zero-latency playback
        self._start_audio, self._start_sr = self._load_audio(self.start_sound_path)
        self._stop_audio, self._stop_sr = self._load_audio(self.stop_sound_path)

        logger.info(
            "SoundFeedback initialized (Start: %s, Stop: %s)",
            self.start_sound_path.name,
            self.stop_sound_path.name,
        )

    def _resolve_sound_file(self, filename: str, default_stem: str) -> Path:
        """Finds configured sound file, or falls back to any file sharing the same stem."""
        exact_path = self.sounds_dir / filename
        if exact_path.exists():
            return exact_path

        # Check for alternative extensions (e.g. start.mp3, start.wav, start.ogg)
        stem = Path(filename).stem or default_stem
        for candidate in self.sounds_dir.glob(f"{stem}.*"):
            if candidate.is_file() and candidate.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
                return candidate

        return exact_path

    def play_start(self, wait: bool = True) -> None:
        """Plays the wake/start listening chime."""
        if self._start_audio is not None and len(self._start_audio) > 0:
            sd.play(self._start_audio, samplerate=self._start_sr)
            if wait:
                sd.wait()
        else:
            logger.warning("Start sound is empty or missing (%s).", self.start_sound_path)

    def play_stop(self, wait: bool = False) -> None:
        """Plays the stop listening / processing chime."""
        if self._stop_audio is not None and len(self._stop_audio) > 0:
            sd.play(self._stop_audio, samplerate=self._stop_sr)
            if wait:
                sd.wait()
        else:
            logger.warning("Stop sound is empty or missing (%s).", self.stop_sound_path)

    def reload(self) -> None:
        """Reload audio files from disk (useful if user replaced them)."""
        self.start_sound_path = self._resolve_sound_file(self.config.start_file, default_stem="start")
        self.stop_sound_path = self._resolve_sound_file(self.config.stop_file, default_stem="stop")
        self._start_audio, self._start_sr = self._load_audio(self.start_sound_path)
        self._stop_audio, self._stop_sr = self._load_audio(self.stop_sound_path)

    def _load_audio(self, file_path: Path) -> tuple[Optional[np.ndarray], int]:
        """Loads a WAV, MP3, or other audio file into a numpy array with clean hardware padding."""
        if not file_path.exists():
            return None, 44100

        audio = None
        sample_rate = 44100

        # 1. Primary method for WAV files: direct lossless read via scipy.io.wavfile
        if file_path.suffix.lower() == ".wav":
            try:
                import warnings
                from scipy.io import wavfile
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    sample_rate, audio = wavfile.read(str(file_path))
            except Exception as e:
                logger.debug("scipy.io.wavfile read failed for %s (%s). Trying wave module.", file_path, e)
                try:
                    with wave.open(str(file_path), "rb") as wf:
                        sample_rate = wf.getframerate()
                        num_frames = wf.getnframes()
                        raw_bytes = wf.readframes(num_frames)
                        sampwidth = wf.getsampwidth()
                        num_channels = wf.getnchannels()

                        if sampwidth == 2:
                            audio = np.frombuffer(raw_bytes, dtype=np.int16)
                        elif sampwidth == 1:
                            audio = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.int16) - 128) * 256
                        else:
                            audio = np.frombuffer(raw_bytes, dtype=np.int16)

                        if num_channels > 1:
                            audio = audio.reshape(-1, num_channels)
                except Exception as we:
                    logger.error("wave fallback failed for %s: %s", file_path, we)

        # 2. For MP3 / compressed formats, decode via PyAV
        if audio is None:
            try:
                from faster_whisper.audio import decode_audio
                audio = decode_audio(str(file_path), sampling_rate=44100)
                sample_rate = 44100
            except Exception as e:
                logger.error("Failed to decode audio file %s: %s", file_path, e)
                return None, 44100

        # 3. Add 200ms tail silence padding so Windows DAC / DirectSound hardware buffer doesn't clip the audio tail
        if audio is not None and len(audio) > 0:
            pad_frames = int(sample_rate * 0.20)
            if audio.ndim == 1:
                padding = np.zeros(pad_frames, dtype=audio.dtype)
            else:
                padding = np.zeros((pad_frames, audio.shape[1]), dtype=audio.dtype)
            audio = np.concatenate([audio, padding])

        return audio, sample_rate

    def _ensure_default_sounds(self) -> None:
        """Synthesizes subtle default UI tones if no start or stop sounds exist."""
        if not self.start_sound_path.exists():
            default_path = self.sounds_dir / "start.wav"
            if not default_path.exists():
                logger.info("Generating default start.wav tone in %s", self.sounds_dir)
                self._generate_chime(
                    frequencies=[523.25, 659.25],  # C5 -> E5 (Rising upbeat chime)
                    durations=[0.08, 0.12],
                    output_path=default_path,
                )
            self.start_sound_path = default_path

        if not self.stop_sound_path.exists():
            default_path = self.sounds_dir / "stop.wav"
            if not default_path.exists():
                logger.info("Generating default stop.wav tone in %s", self.sounds_dir)
                self._generate_chime(
                    frequencies=[659.25, 523.25],  # E5 -> C5 (Gentle falling chime)
                    durations=[0.06, 0.08],
                    output_path=default_path,
                )
            self.stop_sound_path = default_path

    @staticmethod
    def _generate_chime(
        frequencies: list[float],
        durations: list[float],
        output_path: Path,
        sample_rate: int = 44100,
    ) -> None:
        """Synthesizes a soft, clean multi-tone sine wave chime with smooth cosine envelope."""
        tones = []
        for freq, duration in zip(frequencies, durations):
            num_samples = int(sample_rate * duration)
            t = np.linspace(0, duration, num_samples, endpoint=False)
            sine = np.sin(2 * np.pi * freq * t)
            envelope = np.sin(np.pi * np.linspace(0, 1, num_samples)) ** 2
            tone = (sine * envelope * 12000).astype(np.int16)
            tones.append(tone)

        audio = np.concatenate(tones)

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())
