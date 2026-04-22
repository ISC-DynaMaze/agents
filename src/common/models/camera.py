from typing import Literal

from common.models.base import ResponseBase


class CameraResponse(ResponseBase):
    type: Literal["cam-res"] = "cam-res"  # type: ignore
    img: str
