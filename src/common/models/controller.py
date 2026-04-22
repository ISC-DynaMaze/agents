from typing import Annotated, Literal, Union

from pydantic import Field

from common.models.base import RequestBase, ResponseBase


class ControllerRequestBase(RequestBase):
    pass


class ControllerResponseBase(ResponseBase):
    pass


class MazeRequest(ControllerRequestBase):
    type: Literal["ctrl-maze-req"] = "ctrl-maze-req"  # type: ignore


class MazeResponse(ControllerResponseBase):
    type: Literal["ctrl-maze-res"] = "ctrl-maze-res"  # type: ignore
    maze: dict


class AngleRequest(ControllerRequestBase):
    type: Literal["ctrl-angle-req"] = "ctrl-angle-req"  # type: ignore


class AngleResponse(ControllerResponseBase):
    type: Literal["ctrl-angle-res"] = "ctrl-angle-res"  # type: ignore
    id: int
    angle: float


ControllerRequest = Annotated[
    Union[MazeRequest, AngleRequest], Field(discriminator="type")
]
ControllerResponse = Annotated[
    Union[MazeResponse, AngleResponse], Field(discriminator="type")
]
