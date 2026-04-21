from typing import Annotated, Literal, Union

from pydantic import Field, TypeAdapter

from common.models.base import RequestBase
from common.models.camera import CameraResponse
from common.models.logger import LoggerRequest
from common.models.robot import RobotRequest, RobotResponse


class StopRequest(RequestBase):
    type: Literal["stop"] = "stop"  # type: ignore


Request = Annotated[
    Union[
        StopRequest,
        RobotRequest,
        LoggerRequest,
    ],
    Field(discriminator="type"),
]
Response = Annotated[Union[RobotResponse, CameraResponse], Field(discriminator="type")]
ReqRes = Annotated[Union[Request, Response], Field(discriminator="type")]

RequestAdapter = TypeAdapter(Request)
ResponseAdapter = TypeAdapter(Response)
ReqResAdapter = TypeAdapter(ReqRes)
