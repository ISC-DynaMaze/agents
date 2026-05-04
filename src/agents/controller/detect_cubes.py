from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.controller.agent import ControllerAgent
from agents.controller.maze.grid import Maze
from common.models.camera import CameraRequest, CameraResponse
from common.models.common import ReqResAdapter
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class DetectCubesBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("DetectCubesBehaviour")

    async def on_start(self):
        self.logger = self.agent.logger
        self.cubes_dir = Path("cubes")

    async def run(self):
        self.cubes_dir.mkdir(parents=True, exist_ok=True)
        await self.req_image()
        img = await self.wait_for_new_image(timeout=10.0)

        mask = await self.get_mask(img)

        await self.save_img(mask, self.cubes_dir)

    async def get_mask(self, img, threshold=200):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
        return mask

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
        img_path = save_dir / f"cubes_{timestamp}.jpg"
        cv2.imwrite(str(img_path), img)
