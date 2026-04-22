from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

import aiofiles
from spade.behaviour import Message, OneShotBehaviour

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
        data = {"type": "bot-img", "img": encoded_img}
        msg: Message = Message(
            to=self.requester_jid,
            body=json.dumps(data),
            metadata={"performative": "inform"},
        )
        await self.send(msg)
