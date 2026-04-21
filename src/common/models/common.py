from typing import Annotated, Union

from pydantic import Field, TypeAdapter

from common.models.base import RequestBase
from common.models.logger import LoggerRequest
from common.models.robot import RobotRequest, RobotResponse


class StopRequest(RequestBase):
    type = "stop"


Request = Annotated[
    Union[
        StopRequest,
        RobotRequest,
        LoggerRequest,
    ],
    Field(discriminator="type"),
]
Response = Annotated[Union[RobotResponse,], Field(discriminator="type")]
ReqRes = Annotated[Union[Request, Response], Field(discriminator="type")]

RequestAdapter = TypeAdapter(Request)
ResponseAdapter = TypeAdapter(Response)
ReqResAdapter = TypeAdapter(ReqRes)
