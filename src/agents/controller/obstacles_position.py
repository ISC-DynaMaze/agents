from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
import time
import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour
from common.models.camera import CameraRequest, CameraResponse

from agents.controller.get_obstacles import ObstaclesBehaviour

from common.models.common import ReqResAdapter

from agents.controller.maze.detect_obstacles import (
    draw_detected_obstacles,
    find_obstacles,
)

from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent

ROBOT_ARM_POSITION = (394, 328)


class ObstacleRelativePositionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("ObstaclePositionsBehaviour")

    async def on_start(self):
        self.obstacle = ObstaclesBehaviour()
        self.rel_pos = Path("rel_pos")

    async def run(self):
        self.rel_pos.mkdir(parents=True, exist_ok=True)
        await self.req_image()
        img = await self.wait_for_new_image(timeout=10.0)

        detection = find_obstacles(image=img, maze=self.agent.maze, min_area=500)
        blocks_by_color = detection["blocks_by_color"]
        maze = detection["maze"]
        self.agent.maze = maze
        self.logger.info(f"Updated maze with detected obstacles: {maze.obstacles}")

        highlighted = self.draw_elements(img, blocks_by_color, ROBOT_ARM_POSITION)
        await self.save_img(highlighted, self.rel_pos)
        self.logger.info(f"Saved highlighted obstacles image to {self.rel_pos}")

    def draw_elements(self, img, blocks_by_color, robot_pos):
        highlighted = draw_detected_obstacles(img, blocks_by_color)
        cv2.circle(highlighted, (robot_pos[0], robot_pos[1]), 3, (255, 255, 255), -1)
        return highlighted

    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

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
