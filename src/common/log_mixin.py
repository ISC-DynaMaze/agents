from __future__ import annotations

from typing import Optional, Protocol

from spade.behaviour import BehaviourType, Template

from common.models.logger import LogRequest, LogType
from common.sender import BaseSenderBehaviour


class HasAddBehaviourProtocol(Protocol):
    def add_behaviour(
        self, behaviour: BehaviourType, template: Optional[Template] = None  # type: ignore
    ):
        pass


class LogMixin(HasAddBehaviourProtocol):
    _logger_jid: Optional[str] = None
    _sender: Optional[str] = None

    def set_logger_jid(self, logger_jid: str):
        self._logger_jid = logger_jid

    def set_sender(self, sender: str):
        self._sender = sender

    def _log(self, msg: str, log_type: LogType):
        if self._logger_jid is None:
            raise ValueError("Logger JID not set")

        if self._sender is None:
            raise ValueError("Sender not set")

        req: LogRequest = LogRequest(sender=self._sender, msg=msg, log_type=log_type)
        self.add_behaviour(BaseSenderBehaviour(req, self._logger_jid))

    def error(self, msg: str):
        self._log(msg, LogType.ERROR)

    def warning(self, msg: str):
        self._log(msg, LogType.WARNING)

    def info(self, msg: str):
        self._log(msg, LogType.INFO)

    def debug(self, msg: str):
        self._log(msg, LogType.DEBUG)
