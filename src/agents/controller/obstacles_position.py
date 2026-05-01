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
    find_obstacles,
    draw_detected_obstacles
)

from agents.controller.maze.wall_detection import get_pink_mask, find_outer_rectangle

from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent

ROBOT_ARM_POSITION = (394, 328)
MAZE_SIZE = (2200,695) #Measured by hand (Width, Height)

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

        measure = self.compute_distance(img)
        self.logger.info(f"[Measure] L :{measure[0]}, l : {measure[1]}")

        result = find_obstacles(img, self.agent.maze)
        blocks = result["block_by_color"]
        for color, list_of_blocks in blocks.items():
            for block in list_of_blocks:
                center = block["center"]  # C'est un tuple (x, y)
                distance_robot = (abs(center[0]-ROBOT_ARM_POSITION[0])*measure[0],abs(center[1]-ROBOT_ARM_POSITION[1])*measure[1])
                self.logger.info(f"Obstacle {color} founded at {center}, {distance_robot[0]} horizontally away and {distance_robot[1]} vertically away ")

    def compute_distance(self, img: np.darray) -> tuple[float, float] :
        mask = get_pink_mask(img)
        sizes = find_outer_rectangle(mask)

        width = sizes[2] #The longest side
        height = sizes[3] #The shortest side

        ratioW = MAZE_SIZE[0]/width
        ratioH = MAZE_SIZE[1]/height
        return (ratioW, ratioH)


    def draw_elements(self, img, blocks_by_color, robot_pos):
        highlighted = self.draw_detected_obstacles(img, blocks_by_color)
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
