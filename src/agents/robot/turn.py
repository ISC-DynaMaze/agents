from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.turn_calibration import AngleCalibrationBehaviour
from common.calibration import RotationCalibration
from common.models.robot import Direction

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class TurningBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, angle: float, direction: Direction, speed: int = 20):
        super().__init__()
        self.angle = angle
        self.speed = speed
        self.direction = direction
        self.logger = logging.getLogger("TurningBehaviour")

    @property
    def left_calib(self) -> Optional[RotationCalibration]:
        return self.agent.calib.rotation_left

    @property
    def right_calib(self) -> Optional[RotationCalibration]:
        return self.agent.calib.rotation_right

    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot
        self.calib = AngleCalibrationBehaviour()

        if self.direction == Direction.Left and self.left_calib is None:
            self.logger.error("No left rotation calibration, using fallback duration")
            self.agent.error("No left rotation calibration, using fallback duration")

        elif self.direction == Direction.Right and self.right_calib is None:
            self.logger.error("No right rotation calibration, using fallback duration")
            self.agent.error("No right rotation calibration, using fallback duration")

    async def run(self):
        self.bot.setBothPWM(self.speed)

        calib: Optional[RotationCalibration] = None
        if self.direction == Direction.Right:
            self.bot.right()
            calib = self.right_calib
        elif self.direction == Direction.Left:
            self.bot.left()
            calib = self.left_calib
        else:
            self.logger.error("[Direction] Wrong direction given")
            return

        turning_time: float = 0.3
        if calib is not None:
            turning_time = calib.interpolate(self.angle)
        await asyncio.sleep(turning_time)
        self.bot.stop()
