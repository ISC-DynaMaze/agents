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


class PathRequest(ControllerRequestBase):
    type: Literal["ctrl-path-req"] = "ctrl-path-req"  # type: ignore


class PathResponse(ControllerResponseBase):
    type: Literal["ctrl-path-res"] = "ctrl-path-res"  # type: ignore
    path: list[tuple[int, int]]


class ObstaclesRequest(ControllerRequestBase):
    type: Literal["ctrl-obstacles-req"] = "ctrl-obstacles-req"  # type: ignore


class ObstaclesResponse(ControllerResponseBase):
    type: Literal["ctrl-obstacles-res"] = "ctrl-obstacles-res"  # type: ignore


class AngleRequest(ControllerRequestBase):
    type: Literal["ctrl-angle-req"] = "ctrl-angle-req"  # type: ignore


class AngleResponse(ControllerResponseBase):
    type: Literal["ctrl-angle-res"] = "ctrl-angle-res"  # type: ignore
    id: int
    angle: float


class DirectionResponse(ControllerResponseBase):
    type: Literal["ctrl-direction-res"] = "ctrl-direction-res"  # type: ignore
    direction: str


class DirectionRequest(ControllerRequestBase):
    type: Literal["ctrl-direction-req"] = "ctrl-direction-req"  # type: ignore


class ObstaclePositionRequest(ControllerRequestBase):
    type: Literal["ctrl-obs-pos-req"] = "ctrl-obs-pos-req"  # type: ignore


ControllerRequest = Annotated[
    Union[
        MazeRequest,
        AngleRequest,
        PathRequest,
        DirectionRequest,
        ObstaclesRequest,
        ObstaclePositionRequest,
    ],
    Field(discriminator="type"),
]
ControllerResponse = Annotated[
    Union[
        MazeResponse, AngleResponse, PathResponse, DirectionResponse, ObstaclesResponse
    ],
    Field(discriminator="type"),
]
