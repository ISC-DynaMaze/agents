from __future__ import annotations

from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from common.models.controller import MazeResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


# Behaviour to send maze data to requester
class SendMazeBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self, maze):
        super().__init__()
        self.maze = maze

    async def run(self) -> None:
        res = MazeResponse(maze=self.maze.to_dict())
        for requester in self.agent.maze_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))

        self.agent.logger.info(f"Maze data sent to {self.agent.maze_requesters}")
        self.agent.maze_requesters = []
