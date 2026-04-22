from typing import Literal

from common.models.base import RequestBase, ResponseBase


class CameraRequest(RequestBase):
    type: Literal["cam-req"] = "cam-req"  # type: ignore


class CameraResponse(ResponseBase):
    type: Literal["cam-res"] = "cam-res"  # type: ignore
    img: str
