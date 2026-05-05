from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.controller.get_obstacles import ObstaclesBehaviour
from agents.controller.maze.detect_obstacles import find_obstacles
from agents.controller.maze.wall_detection import find_outer_rectangle, get_pink_mask
from common.models.camera import CameraRequest, CameraResponse
from common.sender import BaseSenderBehaviour
from common.utils import wait_for_response

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class ObstacleRelativePositionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("ObstaclePositionsBehaviour")

    async def on_start(self):
        self.obstacle = ObstaclesBehaviour()
        self.rel_pos = Path("rel_pos")
        self.robot_arm_position = self.agent.config.arm_center_pos
        self.maze_size = self.agent.config.maze_real_world_size_m

    async def run(self):
        self.rel_pos.mkdir(parents=True, exist_ok=True)
        await self.req_image()
        img: Optional[np.ndarray] = await self.wait_for_new_image(timeout=10.0)

        if img is None:
            return

        self.logger.info(
            "[Measure] Start calculating pixel distance and real distance on maze border"
        )
        scale = self.compute_scale(img)
        self.logger.info(f"[Measure] L :{scale[0]}, l : {scale[1]}")
        result = find_obstacles(img, self.agent.maze)
        blocks = result["blocks_by_color"]
        blocks_pos = dict()
        for color, list_of_blocks in blocks.items():
            blocks_pos[color] = []
            for block in list_of_blocks:
                center = block["center"]  # That's a tuple (x, y)
                distance_robot = (
                    -(center[0] - self.robot_arm_position[0]) * scale[0], #Need to invert the x axis, the x axis of the picture and the x axis of the robot arm are not the same
                    (center[1] - self.robot_arm_position[1]) * scale[1],
                )
                self.logger.info(
                    f"Obstacle {color} founded at {center}, x: {distance_robot[0]}, y: {distance_robot[1]}")
                blocks_pos[color].append(
                    {"x": distance_robot[0], "y": distance_robot[1]}
                )

        self.save_obstacle_position(blocks_pos)

    def compute_scale(self, img: np.ndarray) -> tuple[float, float]:
        mask = get_pink_mask(img)
        sizes = find_outer_rectangle(mask)
        width = sizes[2]  # The longest side
        height = sizes[3]  # The shortest side

        scaleW = self.maze_size[0] / width
        scaleH = self.maze_size[1] / height
        return (scaleW, scaleH)

    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

    async def wait_for_new_image(self, timeout: float) -> Optional[np.ndarray]:
        res: Optional[CameraResponse] = await wait_for_response(
            self, CameraResponse, timeout
        )
        if res is None:
            self.logger.error("Timed out waiting for camera response message")
            return None
        save_dir = Path("photos")
        img, _ = await res.decode_img(save_dir)
        return img

    def save_obstacle_position(self, block_pos: dict):
        filename = self.rel_pos / "obs_pos.json"
        with open(filename, "w") as f:
            json.dump(block_pos, f, indent=4)
