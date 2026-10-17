"""Desktop OS Action Executor and Router."""

import logging
from src.agent.intent import IntentResult
from src.automation.models import ExecutionResult
from src.automation.handlers import AppHandler, WebHandler, TimeHandler, SystemHandler

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Dispatches validated intents to dedicated desktop action handlers."""

    def __init__(self) -> None:
        self.app_handler = AppHandler()
        self.web_handler = WebHandler()
        self.time_handler = TimeHandler()
        self.system_handler = SystemHandler()

    def execute(self, intent: IntentResult) -> ExecutionResult:
        """Routes an IntentResult to the appropriate action handler."""
        action = intent.action.lower().strip()
        target = (intent.target or "").strip()

        logger.info("Executing action: '%s' with target: '%s'", action, target)

        if action == "open_app":
            return self.app_handler.open_app(target)
        elif action == "web_search":
            return self.web_handler.search(target, raw_query=intent.raw_query)
        elif action == "get_time":
            return self.time_handler.get_time()
        elif action == "system_control":
            return self.system_handler.control(target)
        elif action == "conversation":
            return ExecutionResult(
                success=True,
                action="conversation",
                message="Handled by conversational reply.",
            )
        else:
            logger.warning("Unrecognized action '%s'. Treating as conversation.", action)
            return ExecutionResult(
                success=False,
                action=action,
                message=f"Action '{action}' is not supported.",
            )

    # Backward-compatible delegate methods
    @staticmethod
    def _open_app(target: str) -> ExecutionResult:
        return AppHandler.open_app(target)

    @staticmethod
    def _web_search(query: str, raw_query: str = "") -> ExecutionResult:
        return WebHandler.search(query, raw_query=raw_query)

    @staticmethod
    def _get_time() -> ExecutionResult:
        return TimeHandler.get_time()

    @staticmethod
    def _system_control(command: str) -> ExecutionResult:
        return SystemHandler.control(command)

    @classmethod
    def _set_master_volume_percent(cls, percent: int) -> bool:
        return SystemHandler._set_master_volume_percent(percent)
