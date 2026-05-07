from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np

from agents.controller.maze.grid import Maze
from agents.controller.maze.wall_detection import build_maze_from_path
from common.models.controller import MazeRequest, MazeResponse
from common.request_handler import RequestHandler

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class MazeManager(RequestHandler):
    agent: ControllerAgent

    def __init__(self, agent: ControllerAgent, save_dir: Path):
        super().__init__(agent)
        self.save_dir: Path = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("MazeManager")
        self.maze: Optional[Maze] = None
        self.grid_img: Optional[np.ndarray] = None

    async def do_request(self, req: MazeRequest):
        maze: Optional[Maze] = await self.get_or_fetch()
        if maze is None:
            return
        res: MazeResponse = MazeResponse(maze=maze.to_dict())
        await self.send_response(res)

    async def fetch(self):
        path: Optional[Path] = await self.agent.camera.get_path()

        if path is None:
            self.logger.error("Failed to get image for maze")
            self.agent.error("Failed to get image for maze")
            return

        try:
            result = build_maze_from_path(
                image_path=path,
                bot_id=self.agent.config.bot_aruco_id,
                target_id=self.agent.config.target_aruco_id,
                rows=3,
                cols=11,
                kernel_len=25,
                min_length=30,
                overlap_ratio=0.6,
                cell_size=140,
                margin=40,
                wall_thickness=4,
            )
        except Exception as e:
            self.logger.error(f"Failed to build maze from {path}: {e}")
            self.agent.error(f"Failed to build maze from {path}: {e}")
            return None

        self.maze = result["maze"]
        self.grid_img = result["grid_img"]

        # debug image
        maze_img_path = self.save_dir / f"maze_{path.stem}.jpg"
        cv2.imwrite(str(maze_img_path), self.grid_img)  # type: ignore

        self.logger.info(f"Maze built from {path}")
        self.logger.info(f"Debug maze image saved at {maze_img_path}")

    async def get_or_fetch(self) -> Optional[Maze]:
        if self.maze is None:
            await self.fetch()
        return self.maze
