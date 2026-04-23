from __future__ import annotations

from pathlib import Path
import datetime
import cv2
from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

from agents.controller.maze.find_path import find_path, draw_path
from agents.controller.maze.grid import Maze

from common.models.controller import PathResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class FindPathBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    # reciever would be the controller itself
    def __init__(self, maze: Maze, output_dir: Path):
        super().__init__()
        self.maze = maze
        self.output_dir = output_dir

    async def run(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path_filename = f"path_{timestamp}.jpg"

        if self.maze.bot_cell is None or self.maze.target_cell is None:
            self.agent.logger.error("Bot cell or target cell not set in maze")
            return

        path = find_path(self.maze)
        if path is None:
            self.agent.logger.error("No path found from bot to target")
            return
        self.agent.logger.info(f"Path found: {path}")
        self.agent.current_path = path

        grid_img = self.agent.grid_img.copy()  # type: ignore
        grid_img_with_path = draw_path(
            grid_img, path, cell_size=140, margin=40, color=(0, 0, 0)
        )
        grid_img_path = self.output_dir / path_filename
        cv2.imwrite(str(grid_img_path), grid_img_with_path)
        self.agent.logger.info(f"Path image saved at {grid_img_path}")

        await self.send_path_message(path)
        

    async def send_path_message(self, path: list[tuple[int, int]]):
        res = PathResponse(path=path)
        for requester in self.agent.path_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))
    


  