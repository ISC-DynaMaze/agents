from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

from common.models.camera import CameraRequest
from common.sender import BaseSenderBehaviour


class RequestPhotoBehaviour(OneShotBehaviour):
    agent: Agent

    def __init__(self, camera_jid: str):
        super().__init__()
        self.camera_jid: str = camera_jid

    async def run(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, self.camera_jid))
