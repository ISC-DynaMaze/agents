from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from common.calibration import DistanceCalibration

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class DistanceCalibrationBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, speed: int = 20, check_interval: float = 0.02):
        super().__init__()
        self.logger = logging.getLogger("DistanceCalibration")
        self.logger.setLevel(logging.DEBUG)
        self.speed = speed
        self.check_interval = check_interval

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot
    
    @property
    def threshold(self) -> float:
        return self.agent.config.ir_threshold

    async def run(self) -> None:
        self.bot.setBothPWM(self.speed)
        self.bot.forward()
        line_count: int = 0
        was_on_stud: bool = False
        is_on_stud: bool = False
        last_5_frames: list[int] = []
        start_time: float = 0

        while True:
            # check if at least 1 black stud detected in last 5 frames
            nb_studs: int = self.detect_black_studs()
            last_5_frames.append(nb_studs)
            last_5_frames = last_5_frames[-5:]

            is_on_stud = sum(last_5_frames) > 0

            if not was_on_stud and is_on_stud:
                if line_count == 0:
                    line_count += 1
                    start_time = time.monotonic()
                    self.logger.info("First line detected, starting timer")
                    await asyncio.sleep(0.2)

                else:
                    elapsed_time: float = time.monotonic() - start_time
                    self.logger.info(
                        f"Second line detected, elapsed time: {elapsed_time}"
                    )
                    self.bot.stop()

                    # save timing to file
                    self.save_calibration(elapsed_time)

                    return

            was_on_stud = is_on_stud

            # Keep polling until the black studs are detected, but avoid hammering the sensor.
            await asyncio.sleep(self.check_interval)

    # returns number of black studs detected
    def detect_black_studs(self) -> int:
        # read calibrated values
        sensor_values: list[int] = (
            self.bot.bottom_ir.readCalibrated()
        )  # list of 5 values in [0,1000]
        black_studs: int = 0
        for value in sensor_values:
            if value > self.threshold:
                self.logger.debug(
                    f"Sensor value ({value}) above threshold ({self.threshold}), likely detected black stud"
                )
                black_studs += 1

        return black_studs

    def save_calibration(self, elapsed_time: float):
        self.agent.calib.distance = DistanceCalibration(duration=elapsed_time)
        self.agent.calib.save()
