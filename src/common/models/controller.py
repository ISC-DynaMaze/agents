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


ControllerRequest = Annotated[Union[MazeRequest,], Field(discriminator="type")]
ControllerResponse = Annotated[Union[MazeResponse,], Field(discriminator="type")]
