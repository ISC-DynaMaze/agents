from enum import StrEnum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from common.models.base import RequestBase, ResponseBase


class RobotRequestBase(RequestBase):
    pass


class RobotResponseBase(ResponseBase):
    pass


class RobotMoveRequest(RobotRequestBase):
    type: Literal["bot-move-req"] = "bot-move-req"  # type: ignore


class RobotMoveResponse(RobotResponseBase):
    type: Literal["bot-move-res"] = "bot-move-res"  # type: ignore
    # directions: list[directions]


class PanTiltRequest(RobotRequestBase):
    type: Literal["bot-pan-tilt-req"] = "bot-pan-tilt-req"  # type: ignore
    pan: Optional[float] = None
    tilt: Optional[float] = None


class CameraPhotoRequest(RobotRequestBase):
    type: Literal["bot-cam-photo-req"] = "bot-cam-photo-req"  # type: ignore


class CameraPhotoResponse(RobotResponseBase):
    type: Literal["bot-cam-photo-res"] = "bot-cam-photo-res"  # type: ignore
    img: str


class CameraStatus(BaseModel):
    pan: Optional[float] = None
    tilt: Optional[float] = None


class StatusResponse(RobotResponseBase):
    type: Literal["bot-status-res"] = "bot-status-res"  # type: ignore
    camera: CameraStatus


class Direction(StrEnum):
    Left = "left"
    Right = "right"


class TurningRequest(RobotRequestBase):
    type: Literal["bot-turn-req"] = "bot-turn-req"  # type: ignore
    direction: Direction
    angle: float
    speed: Optional[int] = None


class TurningCalibrationRequest(RobotRequestBase):
    type: Literal["bot-turn-calib-req"] = "bot-turn-calib-req"  # type: ignore


class HonkRequest(RobotRequestBase):
    type: Literal["bot-honk"] = "bot-honk"  # type: ignore


RobotRequest = Annotated[
    Union[
        PanTiltRequest,
        CameraPhotoRequest,
        RobotMoveRequest,
        HonkRequest,
        TurningRequest,
        TurningCalibrationRequest,
    ],
    Field(discriminator="type"),
]

RobotResponse = Annotated[
    Union[CameraPhotoResponse, StatusResponse, RobotMoveResponse],
    Field(discriminator="type"),
]
