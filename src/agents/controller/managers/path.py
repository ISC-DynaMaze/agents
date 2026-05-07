from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import cv2

from agents.controller.maze.find_path import draw_path, find_path
from agents.controller.maze.grid import Maze
from common.models.controller import MazePath, PathRequest, PathResponse
from common.request_handler import RequestHandler

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class PathManager(RequestHandler):
    agent: ControllerAgent

    def __init__(self, agent: ControllerAgent, save_dir: Path):
        super().__init__(agent)
        self.save_dir: Path = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("PathManager")
        self.current_path: Optional[MazePath] = None

    async def do_request(self, req: PathRequest):
        path: Optional[MazePath] = await self.get_or_fetch()
        if path is None:
            return
        res: PathResponse = PathResponse(path=path)
        await self.send_response(res)

    async def fetch(self):
        maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
        if maze is None:
            self.logger.error("Failed to get maze")
            self.agent.error("Failed to get maze")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path_filename = f"path_{timestamp}.jpg"

        if maze.bot_cell is None or maze.target_cell is None:
            self.logger.error("Bot cell or target cell not set in maze")
            self.agent.error("Bot cell or target cell not set in maze")
            return

        path: Optional[MazePath] = find_path(maze)
        if path is None:
            self.logger.error("No path found from bot to target")
            self.agent.error("No path found from bot to target")
            return
        self.logger.info(f"Path found: {path}")
        self.current_path = path

        try:
            grid_img = self.agent.maze_manager.grid_img.copy()  # type: ignore
            grid_img_with_path = draw_path(
                grid_img, path, maze, cell_size=140, margin=40, color=(0, 0, 0)
            )
            grid_img_path = self.save_dir / path_filename
            cv2.imwrite(str(grid_img_path), grid_img_with_path)
            self.logger.info(f"Path image saved at {grid_img_path}")
        except Exception as e:
            self.logger.error(f"Failed to draw path: {e}")

    async def get_or_fetch(self) -> Optional[MazePath]:
        if self.current_path is None:
            await self.fetch()
        return self.current_path
