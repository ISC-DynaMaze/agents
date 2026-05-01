from __future__ import annotations

from typing import TYPE_CHECKING

from agents.robot.camera import CameraBehaviour
from agents.robot.honk import HonkBehaviour
from agents.robot.move import MoveBehaviour
from agents.robot.reposition import RepositionBehaviour
from agents.robot.status import SendStatusBehaviour
from agents.robot.turn import TurningBehaviour
from agents.robot.turn_calibration import AngleCalibrationBehaviour
from common.models.common import Request, StopRequest
from common.models.robot import (
    CameraPhotoRequest,
    HonkRequest,
    LookAroundRequest,
    PanTiltRequest,
    RepositionRequest,
    RobotMoveRequest,
    TurningCalibrationRequest,
    TurningRequest,
)
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
                    self.agent.bot.setCameraTilt(tilt)

                self.agent.add_behaviour(SendStatusBehaviour(self.agent.logger_jid))

            case TurningCalibrationRequest():
                turning_calibration_behaviour = AngleCalibrationBehaviour()
                self.agent.add_behaviour(turning_calibration_behaviour)

            case TurningRequest(direction=direction, angle=angle):
                turning_behaviour = TurningBehaviour(angle, direction)
                self.agent.add_behaviour(turning_behaviour)

            case RobotMoveRequest():
                self.agent.add_behaviour(MoveBehaviour())

            case HonkRequest():
                self.agent.add_behaviour(HonkBehaviour())

            case RepositionRequest():
                self.agent.add_behaviour(RepositionBehaviour())

            case LookAroundRequest():
                await self.agent.look_around_handler.on_request(sender_jid, req)
