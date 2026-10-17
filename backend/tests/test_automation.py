"""Unit tests for ActionExecutor desktop automation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.agent.intent import IntentResult
from src.automation.executor import ActionExecutor, ExecutionResult



def test_get_time():
    executor = ActionExecutor()
    intent = IntentResult(action="get_time", speech_reply="Checking time", raw_query="what time is it")
    res = executor.execute(intent)

    assert res.success is True
    assert res.action == "get_time"
    assert res.spoken_override is not None
    assert "time is" in res.spoken_override.lower()


def test_conversation_no_op():
    executor = ActionExecutor()
    intent = IntentResult(action="conversation", speech_reply="Hello there", raw_query="hello")
    res = executor.execute(intent)

    assert res.success is True
    assert res.action == "conversation"


@patch("webbrowser.open")
def test_web_search_google(mock_browser):
    executor = ActionExecutor()
    intent = IntentResult(action="web_search", target="quantum computing", speech_reply="Searching", raw_query="search quantum computing")
    res = executor.execute(intent)

    assert res.success is True
    assert res.action == "web_search"
    mock_browser.assert_called_once()
    called_url = mock_browser.call_args[0][0]
    assert "google.com/search?q=quantum+computing" in called_url


@patch("webbrowser.open")
def test_web_search_youtube(mock_browser):
    executor = ActionExecutor()
    intent = IntentResult(action="web_search", target="play lofi music on youtube", speech_reply="Playing", raw_query="play lofi music on youtube")
    res = executor.execute(intent)

    assert res.success is True
    mock_browser.assert_called_once()
    called_url = mock_browser.call_args[0][0]
    assert "youtube.com/results?search_query=" in called_url


@patch("subprocess.Popen")
def test_open_app(mock_popen):
    executor = ActionExecutor()
    intent = IntentResult(action="open_app", target="chrome", speech_reply="Opening Chrome", raw_query="open chrome")
    res = executor.execute(intent)

    assert res.success is True
    assert res.action == "open_app"
    mock_popen.assert_called_once()
    assert 'start "" "chrome"' in mock_popen.call_args[0][0]


@patch("ctypes.windll.user32.keybd_event")
def test_system_control_volume_up(mock_keybd):
    executor = ActionExecutor()
    intent = IntentResult(action="system_control", target="volume_up", speech_reply="Increasing volume", raw_query="volume up")
    res = executor.execute(intent)

    assert res.success is True
    assert res.action == "system_control"
    assert mock_keybd.call_count == 10  # 5 keydowns + 5 keyups


@patch.object(ActionExecutor, "_set_master_volume_percent", return_value=True)
def test_system_control_volume_percent(mock_set_vol):
    executor = ActionExecutor()

    # Case 1: "volume_set:45"
    intent1 = IntentResult(action="system_control", target="volume_set:45", raw_query="set volume to 45%")
    res1 = executor.execute(intent1)
    assert res1.success is True
    assert "45%" in res1.message
    mock_set_vol.assert_called_with(45)

    # Case 2: User says "45" without %
    intent2 = IntentResult(action="system_control", target="45", raw_query="volume 45")
    res2 = executor.execute(intent2)
    assert res2.success is True
    assert "45%" in res2.message
    mock_set_vol.assert_called_with(45)

    # Case 3: Target "80%"
    intent3 = IntentResult(action="system_control", target="80%", raw_query="set volume to 80%")
    res3 = executor.execute(intent3)
    assert res3.success is True
    assert "80%" in res3.message
    mock_set_vol.assert_called_with(80)



@patch("ctypes.windll.user32.LockWorkStation")
def test_system_control_lock(mock_lock):
    executor = ActionExecutor()
    intent = IntentResult(action="system_control", target="lock", speech_reply="Locking PC", raw_query="lock computer")
    res = executor.execute(intent)

    assert res.success is True
    mock_lock.assert_called_once()


@patch("webbrowser.open")
def test_open_app_url(mock_browser):
    executor = ActionExecutor()
    intent = IntentResult(action="open_app", target="youtube", speech_reply="Opening YouTube", raw_query="open youtube")
    res = executor.execute(intent)

    assert res.success is True
    assert res.action == "open_app"
    mock_browser.assert_called_once_with("https://www.youtube.com")


@patch("webbrowser.open")
def test_web_search_raw_query_youtube(mock_browser):
    executor = ActionExecutor()
    # LLM gave target "music", but raw_query mentions youtube
    intent = IntentResult(
        action="web_search",
        target="music",
        speech_reply="Opening YouTube and searching for music",
        raw_query="open youtube and search for music",
    )
    res = executor.execute(intent)

    assert res.success is True
    mock_browser.assert_called_once()
    called_url = mock_browser.call_args[0][0]
    assert "youtube.com/results?search_query=music" in called_url


if __name__ == "__main__":
    print("=" * 60)
    print("  Testing ActionExecutor Desktop Actions")
    print("=" * 60)

    executor = ActionExecutor()

    # 1. Test get_time
    time_intent = IntentResult(action="get_time", raw_query="what time is it")
    res_time = executor.execute(time_intent)
    print(f"[+] Time Action:       {res_time.spoken_override} (success={res_time.success})")

    # 2. Test conversation
    chat_intent = IntentResult(action="conversation", raw_query="hello")
    res_chat = executor.execute(chat_intent)
    print(f"[+] Chat Action:       {res_chat.message} (success={res_chat.success})")

    # 3. Test exact volume percentage setting
    vol_intent1 = IntentResult(action="system_control", target="volume_set:45", raw_query="set volume to 45%")
    res_vol1 = executor.execute(vol_intent1)
    print(f"[+] Volume 45% Action: {res_vol1.message}")

    vol_intent2 = IntentResult(action="system_control", target="45", raw_query="volume 45")
    res_vol2 = executor.execute(vol_intent2)
    print(f"[+] Volume 45 Action:  {res_vol2.message}")


    print("\n[SUCCESS] ActionExecutor unit checks passed!")



