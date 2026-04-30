from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent

import logging


class DistanceCalibrationBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, speed: int = 20, check_interval: float = 0.1):
        super().__init__()
        self.logger = logging.getLogger("DistanceCalibration")
        self.logger.setLevel(logging.DEBUG)
        self.speed = speed
        self.check_interval = check_interval

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def on_start(self) -> None:
        self.bottom_ir = self.bot.bottom_ir
        self.bot.setBothPWM(self.speed)

    # check for black studs every 500ms
    async def run(self) -> None:
        self.bot.forward()
        line_count = 0
        passed_first_line = False

        while True:
            if not passed_first_line and await self.detect_black_studs() and line_count == 0:
                passed_first_line = True
                line_count += 1
                timer = datetime.datetime.now()
                self.logger.info("First line detected, starting timer")

            if passed_first_line and await self.detect_black_studs() and line_count == 1:
                elapsed = (datetime.datetime.now() - timer).total_seconds()
                self.logger.info(f"Second line detected, elapsed time: {elapsed}")
                self.bot.stop()
                return

            # Keep polling until the black studs are detected, but avoid hammering the sensor.
            await asyncio.sleep(self.check_interval)

    # return true if likely detected black line, false otherwise
    async def detect_black_studs(self):
        black_studs = 0
        # read calibrated values
        sensor_values = (
            self.bot.bottom_ir.readCalibrated()
        )  # list of 5 values in [0,1000]
        for value in sensor_values:
            if value > 500:
                self.logger.info(
                    f"Sensor value ({value}) above threshold, likely detected black stud"
                )
                black_studs += 1

        if black_studs > 2:
            self.logger.info("Likely detected black line")
            return True
        else:
            return False
