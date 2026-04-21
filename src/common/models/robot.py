from typing import Annotated, Literal, Optional, Union

from pydantic import Field

from models.base import RequestBase, ResponseBase


class RobotRequestBase(RequestBase):
    pass


class RobotResponseBase(ResponseBase):
    pass


class PanTiltRequest(RobotRequestBase):
    type: Literal["bot-pan-tilt-req"] = "bot-pan-tilt-req"  # type: ignore
    pan: Optional[float] = None
    tilt: Optional[float] = None


class CameraPhotoRequest(RobotRequestBase):
    type: Literal["bot-cam-photo-req"] = "bot-cam-photo-req"  # type: ignore


class CameraPhotoResponse(RobotResponseBase):
    type: Literal["bot-cam-photo-res"] = "bot-cam-photo-res"  # type: ignore


RobotRequest = Annotated[
    Union[
        PanTiltRequest,
        CameraPhotoRequest,
    ],
    Field(discriminator="type"),
]

RobotResponse = Annotated[Union[CameraPhotoResponse,], Field(discriminator="type")]
