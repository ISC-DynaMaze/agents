from __future__ import annotations
import json

from agents.controller.agent import ControllerAgent
import logging

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent

class RemoveBigObstaclesBehaviour(OneShotBehaviour):
    agent : ControllerAgent

    async def __init__(self):
        super().__init__()
    
    async def on_start(self):
        self.to_agent = "ur-alphabot23-agent@isc-coordinator2.lan"
        self.logger = logging.getLogger("RemoveBigObstaclesRequest")
            

    async def run(self):
        blocks = self.read_file()
        for b in blocks:
            msg = Message(to=self.to_agent)
            msg.set_metadata("performative", "request")
            msg.body = f"pick {self.b}"
            await self.send(msg)
            self.logger.info(f"[Behaviour] Sent request {msg}")


    def read_file(self) -> list[dict]:
        list_obstacle = []
        with open("rel_pos/obs_pos.json", "r") as f :
            blocks = json.load(f)
            for block in blocks.values():
                for pos in block:
                    list_obstacle.append({"pick" : pos, "place" : {"x": -0.149, "y": -0.315}})
        return list_obstacle