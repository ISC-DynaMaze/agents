from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour
from agents.controller.maze.obstacles import Obstacle

from agents.controller.get_obstacles import ObstaclesBehaviour

from common.models.common import ReqResAdapter
from common.models.controller import (
    ObstaclesResponse,
)

from agents.controller.maze.detect_obstacles import (
    draw_detected_obstacles,
    find_obstacles,
)

from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


ROBOT_ARM_POSITION = (394,328)


class ObstacleRelativePositionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__(self)
        self.logger = logging.getLogger("ObstaclesBehaviour")
    
    async def on_start(self):
        self.obstacle: ObstaclesBehaviour
        self.rel_pos = Path("rel_pos")

    async def run(self):
        await self.obstacle.req_image()
        img = await self.obstacle.wait_for_new_image(timeout=10.0)

        detection = find_obstacles(image=img, maze=self.agent.maze, min_area=500)
        blocks_by_color = detection["blocks_by_color"]
        maze = detection["maze"]
        self.agent.maze = maze
        self.logger.info(f"Updated maze with detected obstacles: {maze.obstacles}")

        # visualize detected obstacles on image
        highlighted = self.draw_elements(self.img, blocks_by_color, ROBOT_ARM_POSITION)
        await self.save_img(highlighted, self.rel_pos)
        self.logger.info(f"Saved highlighted obstacles image to {self.rel_pos}")
    
    def draw_elements(self, img, blocks_by_color, robot_pos):
        
        highlighted = draw_detected_obstacles(img, blocks_by_color)
        cv2.circle(highlighted, (robot_pos[0], robot_pos[1]), 3, (0, 0, 0), -1)
        return highlighted

