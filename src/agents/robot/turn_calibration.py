from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from common.calibration import RotationCalibration, RotationMeasure, RotationTest
from common.models.controller import AngleRequest, AngleResponse
from common.models.robot import Direction
from common.sender import BaseSenderBehaviour
from common.utils import wait_for_response

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class AngleCalibrationBehaviour(OneShotBehaviour):
    agent: RobotAgent

    TEST_ANGLES = [45, 90, 135]

    def __init__(self, time: float = 0.1, speed: float = 20, delta_t: float = 0.05):
        super().__init__()
        self.speed: float = speed
        self.time: float = time
        self.delta_t: float = delta_t
        self.logger = logging.getLogger("AngleCalibrationBehaviour")

    @property
    def bot_id(self) -> int:
        return self.agent.config.bot_aruco_id

    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot

    async def run(self):
        self.agent.calib.rotation_left = await self.calibrate_direction(Direction.Left)
        self.agent.calib.rotation_right = await self.calibrate_direction(
            Direction.Right
        )
        self.agent.calib.save()

    async def ask_angle(self) -> Optional[float]:
        self.logger.debug("[Behaviour] Ask controller for current angle")

        msg = AngleRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(msg, self.agent.controller_jid))

        res: Optional[AngleResponse] = await wait_for_response(self, AngleResponse, 5)
        return res.angles.get(self.bot_id) if res is not None else None

    async def calibrate_direction(
        self, direction: Direction
    ) -> Optional[RotationCalibration]:
        current_angle: Optional[float] = await self.ask_angle()
        if current_angle is None:
            self.logger.error("Could not get current angle")
            return None
        self.bot.setBothPWM(self.speed)

        calibration: RotationCalibration = RotationCalibration(speed=self.speed)
        for i in range(10):
            res = await self.calibration_sequence(
                current_angle, i * self.delta_t, direction
            )
            if res is None:
                self.logger.error("Could not get current angle")
                return None
            measure, current_angle = res
            calibration.add_measure(measure)

        if not calibration.is_valid():
            self.logger.error(f"Invalid calibration: {calibration.measures}")
            self.agent.error(f"Invalid calibration: {calibration.measures}")
            return None
        calibration.compute_coefficients()

        for angle in self.TEST_ANGLES:
            duration: float = calibration.interpolate(angle)
            test: Optional[RotationTest] = await self.test_sequence(
                angle, duration, direction
            )
            if test is not None:
                calibration.add_test(test)

        return calibration

    async def calibration_sequence(
        self,
        last_angle: float,
        delta_t: float,
        direction: Direction,
    ) -> Optional[tuple[RotationMeasure, float]]:
        timing = self.time + delta_t
        self.logger.info(f"[Behaviour] Robot turn left for {timing} second(s)")

        if direction == Direction.Left:
            self.bot.left()
        elif direction == Direction.Right:
            self.bot.right()
        await asyncio.sleep(timing)
        self.bot.stop()
        await asyncio.sleep(1)
        current_angle: Optional[float] = await self.ask_angle()
        if current_angle is None:
            return None

        delta = abs(((last_angle - current_angle + 180) % 360) - 180)
        self.logger.info(f"[Time] Time saved : {timing}")
        return RotationMeasure(angle=delta, time=timing), current_angle

    async def test_sequence(
        self, target: float, duration: float, direction: Direction
    ) -> Optional[RotationTest]:
        start_angle: Optional[float] = await self.ask_angle()
        if start_angle is None:
            self.logger.error("Could not get start angle")
            return None

        if direction == Direction.Left:
            self.bot.left()
        else:
            self.bot.right()
        await asyncio.sleep(duration)
        self.bot.stop()

        await asyncio.sleep(1.5)
        end_angle: Optional[float] = await self.ask_angle()
        if end_angle is None:
            self.logger.error("Could not get end angle")
            return None

        delta: float = abs(((start_angle - end_angle + 180) % 360) - 180)

        return RotationTest(time=duration, target=target, obtained=delta)
