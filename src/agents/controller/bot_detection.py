from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.controller import AngleResponse
from common.sender import MultiSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class BotDetectionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self, img: np.ndarray):
        super().__init__()
        self.img: np.ndarray = img
        self.logger = logging.getLogger("BotDetection")

    async def on_start(self) -> None:
        self.dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dict, self.params)

    async def run(self) -> None:
        corners, ids, rejected = self.detector.detectMarkers(self.img)

        bot_angles: dict[int, float] = {}
        if len(corners) > 0:
            # img2 = self.img.copy()
            # cv2.aruco.drawDetectedMarkers(img2, corners, ids)
            # cv2.imwrite("marker.png", img2)
            ids = ids.flatten()
            bot_angles = self.get_angles_from_markers(corners, ids)

        res: AngleResponse = AngleResponse(angles=bot_angles)
        self.agent.add_behaviour(MultiSenderBehaviour(res, self.agent.angle_requesters))
        self.agent.angle_requesters = []

    def get_angles_from_markers(
        self, corners: Sequence[np.ndarray], ids: np.ndarray
    ) -> dict[int, float]:
        angles: list[tuple[int, float]] = []
        for corner, id in zip(corners, ids):
            tl, tr, br, bl = corner[0]
            v: np.ndarray = bl - tl
            angle = np.atan2(v[1], v[0])
            angles.append((int(id), float(np.degrees(angle))))
        return dict(angles)
