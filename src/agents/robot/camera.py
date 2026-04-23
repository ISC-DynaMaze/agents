from __future__ import annotations

import base64
from typing import TYPE_CHECKING

import aiofiles
from spade.behaviour import OneShotBehaviour

from common.models.robot import CameraPhotoResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent

class CameraBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, requester_jid: str):
        super().__init__()
        self.requester_jid: str = requester_jid

    async def run(self) -> None:
        filename: str = "photo.jpg"
        self.agent.cam.capture_file(filename)
        async with aiofiles.open(filename, "rb") as img_file:
            img_data = await img_file.read()
            encoded_img = base64.b64encode(img_data).decode("utf-8")

        res = CameraPhotoResponse(img=encoded_img)
        self.agent.add_behaviour(BaseSenderBehaviour(res, self.requester_jid))
