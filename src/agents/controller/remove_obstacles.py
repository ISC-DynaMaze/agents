import json

from agents.controller.agent import ControllerAgent
import logging

from spade.behaviour import OneShotBehaviour
from spade.message import Message

class RemoveBigObstaclesBehaviour(OneShotBehaviour):
    agent : ControllerAgent

    async def __init__(self):
        super().__init__()
    
    async def on_start(self):
            self.to_agent = "ur-alphabot23-agent@isc-coordinator2.lan"
            self.logger = logging.getLogger("RemoveBigObstaclesRequest")
            

    async def run(self):
        reply = Message(to=self.to_agent)
        reply.set_metadata("performative", "request")
        reply.body = f"pick {self.data}"
        await self.send(reply)
            
        