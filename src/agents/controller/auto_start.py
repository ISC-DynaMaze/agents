from __future__ import annotations
from spade.behaviour import OneShotBehaviour
from common.models.controller import MazeRequest, PathRequest, ObstaclePositionRequest, ObstacleRemoveRequest
from common.models.robot import RobotMoveRequest
from common.sender import BaseSenderBehaviour

from typing import TYPE_CHECKING

import logging
import asyncio



if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent
    from agents.robot.agent import RobotAgent

class AutoStartBehaviour(OneShotBehaviour):
    agent : ControllerAgent

    def __init__(self, camera_jid, agent_jid, robot_jid):
        super().__init__(self)
        self.logger = logging.getLogger("AutoStartBehaviour")
        self.camera_jid = camera_jid
        self.agent_jid = agent_jid
        self.robot_jid = robot_jid

    async def run(self):
        self.agent.info("[Auto Start] Start...")
        maze_req = MazeRequest()
        path_req = PathRequest()
        move_req = RobotMoveRequest()
        obs_pos = ObstaclePositionRequest()
        obs_rem = ObstacleRemoveRequest()
        self.agent.info("[Request] Maze request sent")
        self.agent.add_behaviour(BaseSenderBehaviour(maze_req, self.camera_jid))
        await asyncio.sleep(2)
        self.agent.info("[Request] Path Request sent")
        self.agent.add_behaviour(BaseSenderBehaviour(path_req, self.agent_jid))
        await asyncio.sleep(2)
        self.agent.info("[Request] Move request sent")
        self.agent.add_behaviour(BaseSenderBehaviour(move_req, self.robot_jid))
        await asyncio.sleep(2)
        self.agent.info("[Request] Obstacle removal sequence request sent")
        self.agent.add_behaviour(BaseSenderBehaviour(obs_pos, self.agent_jid))
        await asyncio.sleep(2)
        self.agent.add_behaviour(BaseSenderBehaviour(obs_rem, self.agent_jid))