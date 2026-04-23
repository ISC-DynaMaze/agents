from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from common.models.base import RequestBase, ResponseBase


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
    img: str


class CameraStatus(BaseModel):
    pan: Optional[float] = None
    tilt: Optional[float] = None


class StatusResponse(RobotResponseBase):
    type: Literal["bot-status-res"] = "bot-status-res"  # type: ignore
    camera: CameraStatus

class TurnCalibrationRequest(RobotRequestBase):
    type : Literal["bot-calib-turn-req"] = "bot-calib-turn-req"

class TurnCalibrationResponse(RobotResponseBase):
    type : Literal["bot-calib-turn-res"] = "bot-calib-turn-res"

RobotRequest = Annotated[
    Union[
        PanTiltRequest,
        CameraPhotoRequest,
        TurnCalibrationRequest,
    ],
    Field(discriminator="type"),
]

RobotResponse = Annotated[
    Union[
        CameraPhotoResponse,
        StatusResponse,
        TurnCalibrationResponse
    ], Field(discriminator="type")
]
