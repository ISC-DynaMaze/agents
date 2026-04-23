from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.robot import SideType

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


DEBUG = os.environ.get("ROBOT_DEBUG", "0") != "0"


class LookAroundBehaviour(OneShotBehaviour):
    agent: RobotAgent

    ANGLES: dict[str, tuple[float, float, float]] = {
        "left": (20, 30, np.radians(135)),
        "right": (-20, 30, np.radians(45)),
        "front": (3, 20, np.radians(0)),
    }

    RECT_ANGLE_THRESH: float = np.radians(20)

    IMG_DIR: Path = Path("images")

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("LookAroundBehaviour")

    async def run(self):
        for side, (pan, tilt, expected_angle) in self.ANGLES.items():
            self.logger.info(f"Looking {side}")
            side_type: SideType = await self.look_and_analyse(
                pan, tilt, expected_angle, side
            )

    async def look_and_analyse(
        self, pan: float, tilt: float, expected_angle: float, side: str
    ) -> SideType:
        self.agent.bot.setCameraPan(pan)
        self.agent.bot.setCameraTilt(tilt)
        await asyncio.sleep(0.2)
        img: np.ndarray = self.agent.cam.capture_array()
        cv2.imwrite(self.IMG_DIR / f"side_{side}.png", img)
        return await self.analyse(img, expected_angle, side)

    async def analyse(
        self, img: np.ndarray, expected_angle: float, side: str
    ) -> SideType:
        self.detect_plinth(img, side)
        self.detect_opening(img, expected_angle, side)
        return SideType.UNKNOWN

    def detect_plinth(self, img: np.ndarray, side: str):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 5
        )
        linesP = cv2.HoughLinesP(
            image=thresh,
            rho=1,
            theta=np.pi / 180,
            threshold=150,
            minLineLength=50,
            maxLineGap=50,
        )

        with_lines = img.copy()
        if linesP is not None:
            for i in range(0, len(linesP)):
                l = linesP[i][0]
                cv2.line(
                    with_lines, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv2.LINE_AA
                )
        cv2.imwrite(self.IMG_DIR / f"lines_{side}.png", with_lines)

    def detect_opening(self, img: np.ndarray, expected_angle: float, side: str):
        expected_vec = np.array([np.cos(expected_angle), np.sin(expected_angle)])

        blurred = cv2.GaussianBlur(img, (11, 11), 5)
        lab_img = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)

        l_bin = np.where(lab_img[..., 0] > 50, 255, 0).astype(np.uint8)

        l, a, b = cv2.split(lab_img)
        _, l_bin = cv2.threshold(l, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        cv2.imwrite(self.IMG_DIR / f"{side}_l_bin.png", l_bin.astype(np.uint8))

        cnts, hrcy = cv2.findContours(l_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        with_cnts = img.copy()
        cv2.drawContours(with_cnts, cnts, -1, (0, 0, 255), 2)
        img_area = img.shape[0] * img.shape[1]

        rects = []
        for cnt in cnts:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            area = cv2.contourArea(box)
            v1 = box[1] - box[0]
            v2 = box[3] - box[0]
            l1 = np.linalg.norm(v1)
            l2 = np.linalg.norm(v2)
            a, b = (l1, l2) if l1 < l2 else (l2, l1)
            box = np.intp(box)
            cv2.drawContours(with_cnts, [box], 0, (0, 255, 255), 1)  # type: ignore
            ratio = b / a
            if ratio < 1 or ratio > 10:
                continue
            area_ratio = area / img_area

            if area_ratio < 0.003 or area_ratio > 0.02:
                continue

            v = v2 if l1 < l2 else v1
            vn = v / np.linalg.norm(v)
            angle = np.acos(np.dot(expected_vec, vn))
            angle2 = np.acos(np.dot(expected_vec, -vn))
            if (
                abs(angle) > self.RECT_ANGLE_THRESH
                and abs(angle2) > self.RECT_ANGLE_THRESH
            ):
                continue
            cv2.drawContours(with_cnts, [box], 0, (0, 255, 0), 2)  # type: ignore
        cv2.imwrite(self.IMG_DIR / f"{side}_rects.png", with_cnts)
