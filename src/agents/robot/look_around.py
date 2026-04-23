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
        "left": (20, 30, 135),
        "front": (3, 20, 0),
        "right": (-20, 30, 45),
    }

    RECT_ANGLE_THRESH: float = np.radians(20)
    IMG_DIR: Path = Path("images")
    INTERVAL_SEC: float = 0.5

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("LookAroundBehaviour")
        self.IMG_DIR.mkdir(parents=True, exist_ok=True)

    async def run(self):
        for side, (pan, tilt, expected_angle) in self.ANGLES.items():
            self.logger.info(f"Looking {side}")
            side_type: SideType = await self.look_and_analyse(
                pan, tilt, expected_angle, side
            )
            self.logger.info(f"Side {side} is {side_type}")

    async def look_and_analyse(
        self, pan: float, tilt: float, expected_angle: float, side: str
    ) -> SideType:
        """Look in the given direction and detect the side type

        Args:
            pan (float): camera pan angle (degrees, -75 to 75)
            tilt (float): camera tilt angle (degrees, 0 to 45)
            expected_angle (float):
                expected angle of the opening / wall (degrees, 0 to 180).
                The angle is given from the horizontal, with the Y axis going down
            side (str): name of the side, used to save debug images

        Returns:
            SideType: the type of side
        """

        self.agent.bot.setCameraPan(pan)
        self.agent.bot.setCameraTilt(tilt)
        await asyncio.sleep(self.INTERVAL_SEC)
        img: np.ndarray = self.agent.cam.capture_array()
        cv2.imwrite(self.IMG_DIR / f"side_{side}.png", img)
        return await self.analyse(img, expected_angle, side)

    async def analyse(
        self, img: np.ndarray, expected_angle: float, side: str
    ) -> SideType:
        """Analyse the given view and detect the type of side

        Args:
            img (np.ndarray): view of the side to analyse
            expected_angle (float):
                expected angle of the opening / wall (degrees, 0 to 180).
                The angle is given from the horizontal, with the Y axis going down
            side (str): name of the side, used to save debug images

        Returns:
            SideType: the type of side
        """

        is_wall = self.detect_plinth(img, expected_angle, side)
        is_open = self.detect_opening(img, expected_angle, side)
        if is_open:
            return SideType.OPEN
        if is_wall:
            return SideType.WALL
        return SideType.UNKNOWN

    def detect_plinth(self, img: np.ndarray, expected_angle: float, side: str) -> bool:
        """Detect whether there is a wall base on the given side

        Args:
            img (np.ndarray): view of the side
            expected_angle (float):
                expected angle of the opening / wall (degrees, 0 to 180).
                The angle is given from the horizontal, with the Y axis going down
            side (str): name of the side, used to save debug images

        Returns:
            bool: whether a wall base was detected
        """

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 5
        )
        cv2.imwrite(self.IMG_DIR / f"thresh_{side}.png", thresh)
        linesP = cv2.HoughLinesP(
            image=thresh,
            rho=1,
            theta=np.pi / 180,
            threshold=150,
            minLineLength=50,
            maxLineGap=50,
        )

        with_lines = img.copy()
        count = 0
        if linesP is not None:
            expected_vec = np.array(
                [np.cos(np.radians(expected_angle)), np.sin(np.radians(expected_angle))]
            )
            for i in range(0, len(linesP)):
                x1, y1, x2, y2 = linesP[i][0]
                p1 = np.array([x1, y1])
                p2 = np.array([x2, y2])
                v = p2 - p1
                cv2.line(with_lines, p1, p2, (0, 255, 255), 2, cv2.LINE_AA)  # type: ignore
                vn = v / np.linalg.norm(v)
                angle = np.acos(np.dot(expected_vec, vn))
                angle2 = np.acos(np.dot(expected_vec, -vn))
                if (
                    abs(angle) > self.RECT_ANGLE_THRESH
                    and abs(angle2) > self.RECT_ANGLE_THRESH
                ):
                    continue
                cv2.line(with_lines, p1, p2, (0, 255, 0), 1, cv2.LINE_AA)  # type: ignore
                count += 1
        self.logger.debug(f"Detected {count} base wall lines")
        cv2.imwrite(self.IMG_DIR / f"lines_{side}.png", with_lines)
        return count > 0

    def detect_opening(self, img: np.ndarray, expected_angle: float, side: str) -> bool:
        """Detect whether there is an opening on the given side

        Args:
            img (np.ndarray): view of the side
            expected_angle (float):
                expected angle of the opening / wall (degrees, 0 to 180).
                The angle is given from the horizontal, with the Y axis going down
            side (str): name of the side, used to save debug images

        Returns:
            bool: whether an opening was detected
        """

        expected_vec = np.array(
            [np.cos(np.radians(expected_angle)), np.sin(np.radians(expected_angle))]
        )

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

        count: int = 0
        for cnt in cnts:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            area = cv2.contourArea(box)
            v1 = box[1] - box[0]
            v2 = box[3] - box[0]
            l1 = np.linalg.norm(v1)
            l2 = np.linalg.norm(v2)

            # Ignore tiny artifacts (4 pixel is arbitrary)
            if l1 < 4 or l2 < 4:
                continue
            a, b = (l1, l2) if l1 < l2 else (l2, l1)
            box = np.intp(box)
            cv2.drawContours(with_cnts, [box], 0, (0, 255, 255), 1)  # type: ignore

            # Keep elongated rectangles
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
            count += 1
        self.logger.debug(f"Detected {count} opening rectangles")
        cv2.imwrite(self.IMG_DIR / f"{side}_rects.png", with_cnts)
        return count > 1
