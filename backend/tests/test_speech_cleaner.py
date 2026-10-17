"""Unit tests for TTS spoken text cleaning and sentence streaming."""

from src.tts.synthesizer import TTSSynthesizer

def test_markdown_stripping():
    sample = "The current CEO of Google is **Sundar\u202fPichai**. He stepped into the role of Google’s CEO in **June\u202f2015** (and later became CEO of Alphabet)."
    cleaned = TTSSynthesizer.clean_spoken_text(sample)
    assert "**" not in cleaned
    assert "Sundar Pichai" in cleaned or "Sundar\u202fPichai" in cleaned
    assert "June 2015" in cleaned or "June\u202f2015" in cleaned
    assert "The current CEO of Google is Sundar Pichai. He stepped into the role of Google’s CEO in June 2015 (and later became CEO of Alphabet)." == cleaned

def test_headers_and_code():
    sample = "### Overview\nHere is `code block` and *italics* with [link](http://test.com)."
    cleaned = TTSSynthesizer.clean_spoken_text(sample)
    assert "###" not in cleaned
    assert "`" not in cleaned
    assert "*" not in cleaned
    assert "Here is and italics with link." in cleaned

if __name__ == "__main__":
    test_markdown_stripping()
    test_headers_and_code()
    print("ALL TESTS PASSED!")
