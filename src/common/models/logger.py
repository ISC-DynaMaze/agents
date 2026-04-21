from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import Field

from common.models.robot import RequestBase


class LogType(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class LogRequest(RequestBase):
    type: Literal["logger-log"] = "logger-log"  # type: ignore
    sender: str
    msg: str
    log_type: LogType = LogType.INFO


LoggerRequest = Annotated[Union[LogRequest], Field(discriminator="type")]
