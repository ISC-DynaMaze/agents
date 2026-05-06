from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.controller import AngleResponse
from common.sender import MultiSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class BotDetector:
    def __init__(self, img: np.ndarray):
        self.img: np.ndarray = img
        self.logger = logging.getLogger("BotDetector")
        self.dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dict, self.params)
        self.detected_corners: list[np.ndarray] = []
        self.detected_ids: list[int] = []

        self.detect()

    def detect(self):
        corners, ids, rejected = self.detector.detectMarkers(self.img)
        self.detected_corners = list(corners)
        self.detected_ids = list(map(int, ids.flatten()))

    def get_angles(self) -> dict[int, float]:
        bot_angles: dict[int, float] = {}
        if len(self.detected_corners) > 0:
            bot_angles = {
                bot_id: self._get_angle_from_marker(corner)
                for bot_id, corner in zip(self.detected_ids, self.detected_corners)
            }
        return bot_angles

    def get_positions(self) -> dict[int, tuple[float, float]]:
        bot_pos: dict[int, tuple[float, float]] = {}

        if len(self.detected_corners) > 0:
            bot_pos = {
                bot_id: self._get_pos_from_marker(corner)
                for bot_id, corner in zip(self.detected_ids, self.detected_corners)
            }
        return bot_pos

    def _get_angle_from_marker(self, corners: np.ndarray) -> float:
        tl, tr, br, bl = corners[0]
        v: np.ndarray = bl - tl
        angle = np.atan2(v[1], v[0])
        return float(np.degrees(angle))

    def _get_pos_from_marker(self, corners: np.ndarray) -> tuple[float, float]:
        center: np.ndarray = np.mean(corners[0], axis=0)
        cx: float = float(center[0])
        cy: float = float(center[1])
        return cx, cy


class BotDetectionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self, img: np.ndarray):
        super().__init__()
        self.logger = logging.getLogger("BotDetection")
        self.detector: BotDetector = BotDetector(img)

    async def run(self) -> None:
        bot_angles: dict[int, float] = self.detector.get_angles()

        res: AngleResponse = AngleResponse(angles=bot_angles)
        self.agent.add_behaviour(MultiSenderBehaviour(res, self.agent.angle_requesters))
        self.agent.angle_requesters = []
