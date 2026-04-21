from typing import Annotated, Union

from pydantic import Field, TypeAdapter

from models.base import RequestBase
from models.robot import RobotRequest, RobotResponse


class StopRequest(RequestBase):
    type = "stop"


Request = Annotated[
    Union[
        StopRequest,
        RobotRequest,
    ],
    Field(discriminator="type"),
]
Response = Annotated[Union[RobotResponse,], Field(discriminator="type")]
ReqRes = Annotated[Union[Request, Response], Field(discriminator="type")]

RequestAdapter = TypeAdapter(Request)
ResponseAdapter = TypeAdapter(Response)
ReqResAdapter = TypeAdapter(ReqRes)
