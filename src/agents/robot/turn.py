import asyncio
import datetime
import json
import logging
from pathlib import Path

import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.turn_calibration import AngleCalibrationBehaviour, Direction


class TurningBehaviour(OneShotBehaviour):
    def __init__(self, angle, direction, speed=20):
        super().__init__()
        self.angle = angle
        self.speed = speed
        self.direction = direction
        self.logger = logging.getLogger("TurningBehaviour")
    
    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot
        self.calib = AngleCalibrationBehaviour()
    
    async def run(self):
        turning_time = 0.0
        self.bot.setBothPWM(self.speed)
        if self.direction:
            self.bot.right()
            test, _ = self.calib.load_latest_data(self.direction)
            config = self.load_profile(test)
            turning_time = self.interpolate(config)
        else:
            self.bot.left()
            test, _ = self.calib.load_latest_data(self.direction)
            config = self.load_profile(test)
            turning_time = self.interpolate(config)
        await asyncio.sleep(turning_time)
        self.bot.stop()
        

    def interpolate(self, config: list[tuple[float, float]]):
        data = np.array(config)
        c = np.polyfit(data[:, 0], data[:, 1], 1)
        self.logger.info(f"coefficients: {c}")
        f = np.poly1d(c)
        time = f(self.angle)
        self.logger.info(f"x={self.angle} y={time}")
        return time

    def load_profile(self, file_path) -> list[tuple[float, float]]:
        with open(file_path, "r") as f:
            data = json.load(f)
            parameters = [[m["angle"], m["time"]] for m in data["measures"]]
            return parameters