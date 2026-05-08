from __future__ import annotations
from spade.behaviour import OneShotBehaviour
from common.models.controller import MazeRequest, PathRequest, ObstaclePositionRequest, ObstacleRemoveRequest
from common.models.robot import RobotMoveRequest
from typing import TYPE_CHECKING

import logging
import asyncio



if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent
    from agents.robot.agent import RobotAgent

class AutoStartBehaviour(OneShotBehaviour):
    ctrl : ControllerAgent
    robot : RobotAgent

    def __init__(self):
        self.logger = logging.getLogger("AutoStartBehaviour")

    async def run(self):
        maze_req = MazeRequest()
        path_req = PathRequest()
        move = RobotMoveRequest()
        obs_pos = ObstaclePositionRequest()
        obs_rem = ObstacleRemoveRequest()
        self.ctrl.info("[Request] Maze request sent")
        self.ctrl.add_behaviour(maze_req)
        await asyncio.sleep(2)
        self.ctrl.info("[Request] Path Request sent")
        self.ctrl.add_behaviour(path_req)
        await asyncio.sleep(2)
        self.ctrl.info("[Request] Move request sent")
        self.robot.add_behaviour(move)
        await asyncio.sleep(2)
        self.ctrl.add_behaviour(obs_pos)
        await asyncio.sleep(2)
        self.ctrl.add_behaviour(obs_rem)
        await asyncio.sleep(2)

