from spade.behaviour import OneShotBehaviour

from common.models.controller import MazeRequest, PathRequest
from common.models.robot import RobotMoveRequest
from typing import TYPE_CHECKING

import logging



if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent
    from agents.robot.agent import RobotAgent

class AutoStartBehaviour(OneShotBehaviour):
    agent : ControllerAgent
    robot : RobotAgent

    def __init__(self):
        self.logger = logging.getLogger("AutoStartBehaviour")

    def run(self):
        maze_req = MazeRequest()
        path_req = PathRequest()
        move = RobotMoveRequest()
        self.agent.info("[Request] Maze request sent")
        self.agent.add_behaviour(maze_req)
        self.agent.info("[Request] Path Request sent")
        self.agent.add_behaviour(path_req)
        self.agent.info("[Request] Move request sent")
        self.robot.add_behaviour(move)

