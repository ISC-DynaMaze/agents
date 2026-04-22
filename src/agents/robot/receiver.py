from __future__ import annotations

from typing import TYPE_CHECKING

from agents.robot.camera import CameraBehaviour
from common.models.common import Request
from common.models.robot import CameraPhotoRequest
from common.receiver import BaseReceiverBehaviour


if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class ReceiverBehaviour(BaseReceiverBehaviour):
    agent: RobotAgent

    async def on_request(self, sender_jid: str, req: Request):
        match req:
            case CameraPhotoRequest():
                camera_behaviour = CameraBehaviour(sender_jid)
                self.agent.add_behaviour(camera_behaviour)
