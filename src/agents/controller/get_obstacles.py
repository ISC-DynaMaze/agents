from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.controller.maze.detect_obstacles import (
    draw_detected_obstacles,
    find_obstacles,
)
from common.models.camera import CameraRequest, CameraResponse
from common.models.common import ReqResAdapter
from common.models.controller import (
    ObstaclesResponse,
)
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class ObstaclesBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("ObstaclesBehaviour")

    async def on_start(self):
        self.obstacles_dir = Path("obstacles")

    async def run(self):
        # check for obstacles directory or create it
        self.obstacles_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"ObstaclesBehaviour")

        # request new image
        await self.req_image()
        img = await self.wait_for_new_image(timeout=10.0)
        if img is None:
            self.logger.error("Timed out waiting for camera image")
            return

        # detect obstacles in maze and update maze
        detection = find_obstacles(image=img, maze=self.agent.maze, min_area=500)
        blocks_by_color = detection["blocks_by_color"]
        maze = detection["maze"]  # maze updated with detected obstacles
        self.agent.maze = maze
        self.logger.info(f"Updated maze with detected obstacles: {maze.obstacles}")

        # visualize detected obstacles on image
        highlighted = draw_detected_obstacles(img, blocks_by_color)
        await self.save_img(highlighted, self.obstacles_dir)
        self.logger.info(f"Saved highlighted obstacles image to {self.obstacles_dir}")

        # returns list of obstacles
        obstacles = self.agent.maze.obstacles
        self.logger.info(f"Detected {len(obstacles)} obstacles in the maze")
        await self.send_obstacles_message()

    async def send_obstacles_message(self):
        res = ObstaclesResponse()
        for requester in self.agent.obstacles_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))
        self.agent.obstacles_requesters = []
        self.agent.requesting_obstacles = False

    # request new image from camera agent
    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

    # wait for a new image file to appear in photo_dir that is not in known_files, then read and return it
    async def wait_for_new_image(self, timeout: float) -> np.ndarray:
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error("Timed out waiting for camera response message")
                    continue
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, CameraResponse)
                save_dir = Path("photos")
                img, _ = await res.decode_img(res.img, save_dir)
                return img
            except Exception as e:
                self.logger.error(
                    f"Error occurred while waiting for camera response: {e}"
                )
                continue

    async def save_img(self, img: np.ndarray, save_dir: Path) -> None:
        self.logger.info(f"Saving image to {save_dir}")
        timestamp = int(time.time())
        img_path = save_dir / f"obstacles_{timestamp}.jpg"
        cv2.imwrite(str(img_path), img)
