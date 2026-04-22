from __future__ import annotations

from typing import TYPE_CHECKING

from agents.robot.camera import CameraBehaviour
from common.models.common import Request, StopRequest
from common.models.robot import CameraPhotoRequest, PanTiltRequest
from common.receiver import BaseReceiverBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class ReceiverBehaviour(BaseReceiverBehaviour):
    agent: RobotAgent

    async def on_request(self, sender_jid: str, req: Request):
        match req:
            case StopRequest():
                await self.agent.stop()

            case CameraPhotoRequest():
                camera_behaviour = CameraBehaviour(sender_jid)
                self.agent.add_behaviour(camera_behaviour)

            case PanTiltRequest(pan=pan, tilt=tilt):
                if pan is not None:
                    self.agent.bot.setCameraPan(pan)

                if tilt is not None:
                    self.agent.bot.setCameraPan(tilt)
