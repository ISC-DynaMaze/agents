from __future__ import annotations

from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent

import logging


class DistanceCalibrationBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, speed: int):
        super().__init__()
        self.logger = logging.getLogger("DistanceCalibration")
        self.logger.setLevel(logging.DEBUG)
        self.speed = speed

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def on_start(self) -> None:
        self.bottom_ir = self.bot.bottom_ir
        self.time = 0

    async def run(self) -> None:
        await self.detect_black_studs()

    async def detect_black_studs(self):
        # read calibrated values
        sensor_values = (
            self.bot.bottom_ir.readCalibrated()
        )  # list of 5 values in [0,1000]
        for value in sensor_values:
            # if value > 500:
            self.logger.info(f"Sensor value is {value}")
