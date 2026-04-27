import asyncio
import datetime
import json
from pathlib import Path

import logger
import numpy as np
from spade.behaviour import OneShotBehaviour
from agents.robot.turn_calibration import AngleCalibrationBehaviour

from agents.robot.AlphaBot2 import AlphaBot2

def TurningBehaviour(OneShotBehaviour):
    def __init__(self, angle, direction, speed=20):
        super().__init__()
        self.angle = angle
        self.speed = speed
        self.direction = direction
    
    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot
        self.calib : AngleCalibrationBehaviour
    
    async def run(self):
        config = load_profile(self.calib.load_latest_data()[0])
        turning_time = interpolate(config)
        self.bot.setBothPWM(self.speed)
        if self.direction:
            self.bot.right()
        else:
            self.bot.left()
        await asyncio.sleep(turning_time)
        self.bot.stop()

    def interpolate(self, file):
        return np.interp(self.angle, file[0], file[1])

    def load_profile(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                parameters = [[m["angle"], m["time"]] for m in data["measures"]]
                logger.info(f"[Load] Existing config loaded ")
                return parameters
        except Exception as e:
            logger.error(f"[Load] Erreur : {e}")
            return False
