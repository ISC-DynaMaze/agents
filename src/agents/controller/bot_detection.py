from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.controller import AngleResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class BotDetectionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self, img: np.ndarray):
        super().__init__()
        self.img: np.ndarray = img
        self.logger = logging.getLogger("BotDetection")

    async def run(self) -> None:
        corners, ids, rejected = self.detector.detectMarkers(self.img)

        if len(corners) > 0:
            # img2 = self.img.copy()
            # cv2.aruco.drawDetectedMarkers(img2, corners, ids)
            # cv2.imwrite("marker.png", img2)
            ids = ids.flatten()
            bot_angles: list[tuple[int, float]] = self.get_angles_from_markers(
                corners, ids
            )
            for bot_id, angle in bot_angles:
                await self.send_angle_message(bot_id, angle)

        self.agent.angle_requesters = []

    async def on_start(self) -> None:
        self.dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dict, self.params)

    def get_angles_from_markers(
        self, corners: Sequence[np.ndarray], ids: np.ndarray
    ) -> list[tuple[int, float]]:
        angles: list[tuple[int, float]] = []
        for corner, id in zip(corners, ids):
            tl, tr, br, bl = corner[0]
            v: np.ndarray = bl - tl
            angle = np.atan2(v[1], v[0])
            angles.append((int(id), float(np.degrees(angle))))
        return angles

    async def send_angle_message(self, bot_id: int, angle: float):
        res = AngleResponse(id=bot_id, angle=angle)
        for requester in self.agent.angle_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))
