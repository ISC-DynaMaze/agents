import json
import logging
from typing import Sequence

import cv2
import numpy as np
from spade.agent import Agent
from spade.behaviour import Message, OneShotBehaviour


class BotDetectionBehaviour(OneShotBehaviour):
    agent: Agent

    def __init__(self, img: np.ndarray):
        super().__init__()
        self.img: np.ndarray = img
        self.logger = logging.getLogger("BotDetection")

    async def run(self) -> None:
        corners, ids, rejected = self.detector.detectMarkers(self.img)

        if len(corners) > 0:
            img2 = self.img.copy()
            cv2.aruco.drawDetectedMarkers(img2, corners, ids)
            cv2.imwrite("marker.png", img2)
            bot_angles: list[tuple[int, float]] = self.get_angles_from_markers(
                corners, ids
            )
            for bot_id, angle in bot_angles:
                await self.send_angle_message(bot_id, angle)

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
        data = {"action": "bot-rot", "id": bot_id, "angle": angle}
        msg: Message = Message(
            to=str(self.agent.jid),
            metadata={"performative": "inform"},
            body=json.dumps(data),
        )
        await self.send(msg)
