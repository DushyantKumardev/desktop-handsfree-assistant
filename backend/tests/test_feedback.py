"""Unit tests for SoundFeedback cue player."""

import sys
from pathlib import Path
from unittest.mock import patch

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.audio.feedback import SoundFeedback


def test_sound_feedback_generates_defaults(tmp_path: Path):
    feedback = SoundFeedback(sounds_dir=tmp_path)

    assert (tmp_path / "start.wav").exists()
    assert (tmp_path / "stop.wav").exists()
    assert feedback._start_audio is not None
    assert feedback._stop_audio is not None
    assert feedback._start_sr == 44100
    assert feedback._stop_sr == 44100


def test_sound_feedback_loads_existing_assets():
    """Verify that existing start.mp3 and stop.mp3 in assets are loaded without error."""
    feedback = SoundFeedback()
    assert feedback.start_sound_path.exists()
    assert feedback.stop_sound_path.exists()
    assert feedback._start_audio is not None
    assert feedback._stop_audio is not None


@patch("sounddevice.play")
@patch("sounddevice.wait")
def test_sound_feedback_play(mock_wait, mock_play, tmp_path: Path):
    feedback = SoundFeedback(sounds_dir=tmp_path)

    feedback.play_start(wait=True)
    mock_play.assert_called_once()
    mock_wait.assert_called_once()

    mock_play.reset_mock()
    mock_wait.reset_mock()

    feedback.play_stop(wait=False)
    mock_play.assert_called_once()
    mock_wait.assert_not_called()


if __name__ == "__main__":
    print("=" * 60)
    print("  Testing SoundFeedback Audio Cues (MP3 & WAV)")
    print("=" * 60)

    feedback = SoundFeedback()
    print(f"[+] Loaded start sound: {feedback.start_sound_path} (exists={feedback.start_sound_path.exists()})")
    print(f"[+] Loaded stop sound:  {feedback.stop_sound_path} (exists={feedback.stop_sound_path.exists()})")
    print(f"[+] Start samples:      {len(feedback._start_audio) if feedback._start_audio is not None else 0}")
    print(f"[+] Stop samples:       {len(feedback._stop_audio) if feedback._stop_audio is not None else 0}")

    print("\n[+] Playing start sound...")
    feedback.play_start(wait=True)

    print("[+] Playing stop sound...")
    feedback.play_stop(wait=True)

    print("\n[SUCCESS] SoundFeedback verified successfully!")

