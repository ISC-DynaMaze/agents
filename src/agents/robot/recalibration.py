


import logging

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.agent import RobotAgent
from spade.behaviour import OneShotBehaviour

from common.models.common import ReqResAdapter
from common.models.controller import AngleResponse


class RecalibrateBehaviour(OneShotBehaviour):
    agent: RobotAgent
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("RecalibrateBehaviour")
        self.actual_angle = None

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot
    

    async def wait_angle_response(self, timeout):
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error(
                        "Timed out waiting for direction response message"
                    )
                    return None
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, AngleResponse)
                return res.angle
            except Exception as e:
                self.logger.error(f"Error occurred while waiting for angle: {e}")
                continue