import asyncio
import logging
from typing import TYPE_CHECKING

import cv2
from spade.behaviour import OneShotBehaviour


if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class PanoBehaviour(OneShotBehaviour):
    agent: RobotAgent
    START_PAN = 30
    END_PAN = -30
    MIN_TILT = -30
    MAX_TILT = 20
    IMAGES = 7

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("PanoBehaviour")

    async def run(self) -> None:
        imgs = []
        pan_step: float = (self.END_PAN - self.START_PAN) / self.IMAGES
        mid_i: float = (self.IMAGES - 1) / 2
        tilt_step: float = (self.MAX_TILT - self.MIN_TILT) / mid_i

        for i in range(self.IMAGES):
            pan = self.START_PAN + pan_step
            tilt = self.MAX_TILT - abs(i - mid_i) * tilt_step
            self.agent.bot.setCameraPan(pan)
            self.agent.bot.setCameraTilt(tilt)
            await asyncio.sleep(0.2)
            img = self.agent.cam.capture_array()
            imgs.append(img)
        
        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        status, pano = stitcher.stitch(imgs)

        if status != cv2.Stitcher_OK:
            self.logger.error("Can't stitch images, error code = %d" % status)
            return

        cv2.imwrite("pano.png", pano)
