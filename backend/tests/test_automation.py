"""Unit tests for ActionExecutor and ToolRegistry desktop automation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.tools.models import ToolCall
from src.automation.executor import ActionExecutor, ExecutionResult


def test_get_time():
    executor = ActionExecutor()
    call = ToolCall(name="get_time_date")
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "get_time"
    assert res.spoken_override is not None
    assert "time is" in res.spoken_override.lower()


@patch("src.automation.handlers.web_handler.WebHandler._search_via_serper", return_value="Quantum computing uses qubits to calculate exponentially faster.")
def test_web_search_headless(mock_serper):
    executor = ActionExecutor()
    call = ToolCall(name="web_search", args={"query": "quantum computing"})
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "web_search"
    assert res.spoken_override is not None
    assert "qubits" in res.spoken_override


@patch("webbrowser.open")
def test_play_media_youtube(mock_browser):
    executor = ActionExecutor()
    call = ToolCall(name="play_media", args={"query": "lofi music on youtube"})
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "web_search"
    mock_browser.assert_called_once()
    called_url = mock_browser.call_args[0][0]
    assert "youtube.com/results?search_query=" in called_url


@patch("subprocess.Popen")
def test_open_app_chrome(mock_popen):
    executor = ActionExecutor()
    call = ToolCall(name="open_app", args={"app_name": "chrome"})
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "open_app"
    mock_popen.assert_called_once()
    assert "chrome" in mock_popen.call_args[0][0]


@patch("ctypes.windll.user32.keybd_event")
def test_volume_adjust(mock_keybd):
    executor = ActionExecutor()
    call = ToolCall(name="adjust_volume", args={"direction": "up"})
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "system_control"
    assert mock_keybd.call_count > 0


@patch("src.automation.handlers.system_handler.SystemHandler._set_master_volume_percent")
def test_volume_set_percentage(mock_vol_setter):
    mock_vol_setter.return_value = True
    executor = ActionExecutor()

    call = ToolCall(name="set_volume", args={"level": 45})
    res = executor.execute_tool(call)
    assert res.success is True
    assert res.action == "system_control"
    mock_vol_setter.assert_called_with(45)


@patch("ctypes.windll.user32.LockWorkStation")
def test_lock_workstation(mock_lock):
    mock_lock.return_value = 1
    executor = ActionExecutor()
    call = ToolCall(name="lock_computer")
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "system_control"
    mock_lock.assert_called_once()


@patch("webbrowser.open")
def test_open_youtube_shortcut(mock_browser):
    executor = ActionExecutor()
    call = ToolCall(name="open_app", args={"app_name": "youtube"})
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "open_app"
    mock_browser.assert_called_once_with("https://www.youtube.com")


@patch("ctypes.windll.user32.keybd_event")
def test_media_control_play_pause(mock_keybd):
    executor = ActionExecutor()
    call = ToolCall(name="media_control", args={"command": "play_pause"})
    res = executor.execute_tool(call)

    assert res.success is True
    assert res.action == "system_control"
    assert mock_keybd.call_count > 0


def test_batch_tool_execution():
    executor = ActionExecutor()
    calls = [
        ToolCall(name="get_time_date"),
        ToolCall(name="set_volume", args={"level": 50}),
    ]
    with patch("src.automation.handlers.system_handler.SystemHandler._set_master_volume_percent", return_value=True):
        results = executor.execute_tools(calls)
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True


if __name__ == "__main__":
    print("[*] Running desktop action tool tests...")
    test_get_time()
    test_web_search_headless()
    test_play_media_youtube()
    test_open_app_chrome()
    test_volume_adjust()
    test_volume_set_percentage()
    test_lock_workstation()
    test_open_youtube_shortcut()
    test_media_control_play_pause()
    test_batch_tool_execution()
    print("[SUCCESS] All native tool automation tests passed successfully!")
