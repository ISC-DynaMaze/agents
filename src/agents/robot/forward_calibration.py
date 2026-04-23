import logger
import asyncio

from spade.behaviour import OneShotBehaviour
from .AlphaBot2 import AlphaBot2
from agents.robot.AlphaBot2 import AlphaBot2
from common.models.common import ReqResAdapter
from common.models.controller import AngleRequest, AngleResponse
from common.sender import BaseSenderBehaviour


class ForwardCalibrationBehaviour(OneShotBehaviour):
    def __init__(self):
        super.__init__()
        self.actual_angle = None
    
    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot
    
    async def run(self):
        self.actual_angle = self.ask_angle()
        logger.info(f"[Angle] {self.actual_angle}")
        self.bot.setBothPWM(20)
        self.bot.forward()
        await asyncio.sleep()
        self.bot.stop()
        self.actual_angle() = self.actual_angle()
        logger.info(f"[Angle] {self.actual_angle}")
    
    async def ask_angle(self):
        logger.debug("[Behaviour] Ask controller for actual angle")

        msg = AngleRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(msg, "camera@isc-coordinator.lan"))

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