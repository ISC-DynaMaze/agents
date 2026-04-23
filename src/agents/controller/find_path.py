from __future__ import annotations

from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from agents.controller.find_path import find_path
from agents.controller.walls.grid import Maze

from common.models.controller import PathResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class FindPathBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    # reciever would be the controller itself
    def __init__(self, maze: Maze):
        super().__init__()
        self.maze = maze

    async def run(self) -> None:
        if self.maze.bot_cell is None or self.maze.target_cell is None:
            self.agent.logger.error("Bot cell or target cell not set in maze")
            return

        path = find_path(self.maze)
        if path is None:
            self.agent.logger.error("No path found from bot to target")
            return
        self.agent.logger.info(f"Path found: {path}")

        await self.send_path_message(path)
        

    async def send_path_message(self, path: list[tuple[int, int]]):
        res = PathResponse(path=path)
        for requester in self.agent.path_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))
    


  