from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent

import logging


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

    async def on_start(self) -> None:
        self.bottom_ir = self.bot.bottom_ir
        self.bot.setBothPWM(self.speed)
        self.elapsed_time = 0
        self.output_dir = Path("calibration_data")
        self.path = Path("distance_calibration_data.json")

    # check for black studs every 500ms
    async def run(self) -> None:
        self.bot.forward()
        line_count = 0
        was_on_stud = False
        is_on_stud = False
        last_5_frames = []

        while True:
            # check if at least 1 black stud detected in last 5 frames
            nb_studs = self.detect_black_studs()
            last_5_frames.append(nb_studs)
            last_5_frames = last_5_frames[-5:]

            is_on_stud = sum(last_5_frames) > 0

            if not was_on_stud and is_on_stud:
                if line_count == 0:
                    line_count += 1
                    timer = time.monotonic()
                    self.logger.info("First line detected, starting timer")
                    await asyncio.sleep(0.2)

                elif line_count == 1:
                    self.elapsed_time = time.monotonic() - timer
                    self.logger.info(
                        f"Second line detected, elapsed time: {self.elapsed_time}"
                    )
                    self.bot.stop()

                    # save timing to file
                    data = {"distance_time": self.elapsed_time}
                    self.save_file(data)

                    return

            was_on_stud = is_on_stud

            # Keep polling until the black studs are detected, but avoid hammering the sensor.
            await asyncio.sleep(self.check_interval)

    # returns number of black studs detected
    def detect_black_studs(self):
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

        return black_studs

    def save_file(self, data):
        self.path.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / self.path
        with open(filepath, "w") as f:
            json.dump(data, f)
        self.logger.info(f"Saved calibration data to {filepath}")
