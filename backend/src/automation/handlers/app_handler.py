"""Desktop application and shortcut launcher handler."""

import logging
import subprocess
import webbrowser
from src.automation.models import ExecutionResult

logger = logging.getLogger(__name__)

# Common desktop application aliases mapped to launch commands, PATH executables, or URIs
APP_COMMANDS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "brave": "brave",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "spotify": "spotify",
    "file explorer": "explorer",
    "explorer": "explorer",
    "files": "explorer",
    "terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "settings": "ms-settings:",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "whatsapp:",
}


class AppHandler:
    """Handles launching desktop applications and registered protocol URIs."""

    @staticmethod
    def open_app(target: str) -> ExecutionResult:
        """Launches a desktop application on Windows."""
        if not target:
            return ExecutionResult(success=False, action="open_app", message="No application name specified.")

        clean_target = target.lower().strip()
        cmd = APP_COMMANDS.get(clean_target, clean_target)

        try:
            # If target is a URL, open directly in default browser
            if cmd.startswith("http://") or cmd.startswith("https://"):
                webbrowser.open(cmd)
            else:
                # Use Windows 'start' via cmd so URI schemes and PATH executables launch cleanly
                subprocess.Popen(f'start "" "{cmd}"', shell=True)

            return ExecutionResult(
                success=True,
                action="open_app",
                message=f"Successfully launched {target}.",
            )
        except Exception as e:
            logger.error("Failed to launch application '%s': %s", target, e)
            return ExecutionResult(
                success=False,
                action="open_app",
                message=f"Failed to launch {target}: {e}",
            )
