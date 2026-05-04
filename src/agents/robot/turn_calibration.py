from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from common.calibration import RotationCalibration, RotationMeasure, RotationTest
from common.models.common import ReqResAdapter
from common.models.controller import AngleRequest, AngleResponse
from common.models.robot import Direction
from common.sender import BaseSenderBehaviour

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

    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot

    async def run(self):
        self.agent.calib.rotation_left = await self.calibrate_direction(Direction.Left)
        self.agent.calib.rotation_right = await self.calibrate_direction(
            Direction.Right
        )
        self.agent.calib.save()

    async def ask_angle(self) -> float:
        self.logger.debug("[Behaviour] Ask controller for actual angle")

        msg = AngleRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(msg, self.agent.controller_jid))

        while True:
            reply = await self.receive(timeout=5)
            try:
                assert reply is not None
                res = ReqResAdapter.validate_json(reply.body)
                assert isinstance(res, AngleResponse)
                break
            except:
                continue
        return res.angle

    async def calibrate_direction(
        self, direction: Direction
    ) -> Optional[RotationCalibration]:
        current_angle: float = await self.ask_angle()
        self.bot.setBothPWM(self.speed)

        calibration: RotationCalibration = RotationCalibration(speed=self.speed)
        for i in range(10):
            measure, current_angle = await self.calibration_sequence(
                current_angle, i * self.delta_t, direction
            )
            calibration.add_measure(measure)

        calibration.compute_coefficients()

        for angle in self.TEST_ANGLES:
            duration: float = calibration.interpolate(angle)
            test: RotationTest = await self.test_sequence(angle, duration, direction)
            calibration.add_test(test)

        return calibration

    async def calibration_sequence(
        self,
        last_angle: float,
        delta_t: float,
        direction: Direction,
    ) -> tuple[RotationMeasure, float]:
        timing = self.time + delta_t
        self.logger.info(f"[Behaviour] Robot turn left for {timing} second(s)")

        if direction == Direction.Left:
            self.bot.left()
        elif direction == Direction.Right:
            self.bot.right()
        await asyncio.sleep(timing)
        self.bot.stop()
        await asyncio.sleep(1)
        current_angle: float = await self.ask_angle()

        delta = abs(((last_angle - current_angle + 180) % 360) - 180)
        self.logger.info(f"[Time] Time saved : {timing}")
        return RotationMeasure(angle=delta, time=timing), current_angle

    def interpolate(self, delta_history: list[list[float]]) -> list[float]:
        x = []
        y = []
        for c in delta_history:
            x.append(c[0])
            y.append(c[1])
        return np.interp([45, 90, 135], x, y)  # type: ignore

    async def test_sequence(
        self, target: float, duration: float, direction: Direction
    ) -> RotationTest:
        start_angle: float = await self.ask_angle()

        if direction == Direction.Left:
            self.bot.left()
        else:
            self.bot.right()
        await asyncio.sleep(duration)
        self.bot.stop()

        await asyncio.sleep(1.5)
        end_angle: float = await self.ask_angle()

        delta: float = abs(((start_angle - end_angle + 180) % 360) - 180)

        return RotationTest(time=duration, target=target, obtained=delta)
