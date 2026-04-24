import asyncio
import logging
import json
import datetime
from pathlib import Path

from spade.behaviour import OneShotBehaviour
from .AlphaBot2 import AlphaBot2
from agents.robot.AlphaBot2 import AlphaBot2
from common.models.common import ReqResAdapter
from common.models.controller import AngleRequest, AngleResponse
from common.sender import BaseSenderBehaviour


class ForwardCalibrationBehaviour(OneShotBehaviour):
    def __init__(self, speed=20, speed_variation=0.5):
        super().__init__()
        self.actual_angle = None
        self.speed_variation = speed_variation
        self.speed = speed
        self.logger = logging.getLogger("ForwardCalibrationBehaviour")
    
    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot
    
    async def run(self):
        data = await self.speed_influence()
        self.save_data(data)
    
    async def speed_influence(self):
        angle_history = []
        delta_history = dict()
        for i in range(1):
            self.actual_angle = await self.ask_angle()
            angle_history.append(self.actual_angle)
            self.logger.info(f"[Angle] {self.actual_angle}")
            self.speed = self.speed + self.speed_variation
            self.bot.setBothPWM(self.speed)
            self.bot.forward()
            await asyncio.sleep(2-i*self.speed_variation/5)
            self.bot.stop()
            self.actual_angle = await self.ask_angle()
            await asyncio.sleep(5)
            angle_history.append(self.actual_angle)
            self.logger.info(f"[Angle] {self.actual_angle}")
            delta = ((angle_history[-1] - angle_history[-2] + 180) % 360) - 180
            delta_history[self.speed]=delta
        return delta_history

    def save_data(self, dct):
        save_path = Path("test_result")
        save_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = save_path / f"debug_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(dct,f)
            

    async def ask_angle(self):
        self.logger.debug("[Behaviour] Ask controller for actual angle")

        msg = AngleRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(msg, "alberto-ctrl@isc-coordinator.lan"))

        while True:
            reply = await self.receive(timeout=15)
            try:
                assert reply is not None
                res = ReqResAdapter.validate_json(reply.body)
                assert isinstance(res, AngleResponse)
                break
            except:
                continue
        return res.angle