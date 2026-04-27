import asyncio
import datetime
import json
import logging
from pathlib import Path

import numpy as np
from spade.behaviour import OneShotBehaviour
from agents.robot.turn_calibration import AngleCalibrationBehaviour
from agents.robot.AlphaBot2 import AlphaBot2

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
        test, _ = self.calib.load_latest_data()
        config = self.load_profile(test)
        turning_time = self.interpolate(config)
        self.bot.setBothPWM(self.speed)
        if self.direction:
            self.bot.right()
        else:
            self.bot.left()
        await asyncio.sleep(turning_time)
        self.bot.stop()
        

    def interpolate(self, file):
        f = np.polyfit(file[0], file[1], 1)
        return f(self.angle)

    def load_profile(self, file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            parameters = [[m["angle"], m["time"]] for m in data["measures"]]
            return parameters