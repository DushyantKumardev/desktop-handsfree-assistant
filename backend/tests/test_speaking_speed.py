"""Test for dynamic TTS speaking speed tool."""

from src.tts.synthesizer import TTSSynthesizer
from src.tools.handlers import set_speaking_speed

def test_speaking_speed_tool():
    synth = TTSSynthesizer()
    initial_speed = synth.speed
    print(f"Initial speed: {initial_speed}x")

    # Test faster
    res = set_speaking_speed.execute("faster")
    assert res.success is True
    assert synth.speed > initial_speed
    print(f"Faster speed: {synth.speed}x, spoken: '{res.spoken_override}'")

    # Test slower
    res = set_speaking_speed.execute("slower")
    assert res.success is True
    print(f"Slower speed: {synth.speed}x, spoken: '{res.spoken_override}'")

    # Test normal reset
    res = set_speaking_speed.execute("normal")
    assert res.success is True
    assert synth.speed == 1.15
    print(f"Normal speed: {synth.speed}x, spoken: '{res.spoken_override}'")

    # Test numeric speed
    res = set_speaking_speed.execute("1.5")
    assert res.success is True
    assert synth.speed == 1.5
    print(f"Exact 1.5x speed: {synth.speed}x")

    # Test persistence across new synthesizer instance
    synth2 = TTSSynthesizer()
    assert synth2.speed == 1.5
    print(f"Persisted speed in new instance: {synth2.speed}x")

    # Reset back to default
    set_speaking_speed.execute("normal")
    assert synth.speed == 1.15
    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_speaking_speed_tool()
