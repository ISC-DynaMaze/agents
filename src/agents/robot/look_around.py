from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Union

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.robot import (
    CubesResult,
    LookAroundRequest,
    LookAroundResponse,
    SideType,
)
from common.request_handler import RequestHandler

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


DEBUG = os.environ.get("ROBOT_DEBUG", "0") != "0"

SideStr = Union[Literal["front"], Literal["left"], Literal["right"]]
Segment = tuple[np.ndarray, np.ndarray]


@dataclass
class SideConfig:
    pan: float
    tilt: float
    expected_angle: float


@dataclass
class CubeChannelConfig:
    space: int
    channel: int
    inverted: bool


class LookAroundBehaviour(OneShotBehaviour):
    agent: RobotAgent

    ANGLES: dict[SideStr, list[SideConfig]] = {
        "left": [
            SideConfig(30, 30, 135),
            SideConfig(25, 35, 135),
            SideConfig(20, 30, 135),
        ],
        "front": [
            SideConfig(0, 20, 0),
            SideConfig(0, 25, 0),
            SideConfig(0, 30, 0),
        ],
        "right": [
            SideConfig(-30, 30, 45),
            SideConfig(-35, 35, 45),
            SideConfig(-40, 30, 45),
        ],
    }

    RECT_ANGLE_THRESH: float = np.radians(20)
    IMG_DIR: Path = Path("images")
    INTERVAL_SEC: float = 0.5
    MIN_OPENING_RECTS: float = 1
    MIN_PLINTH_LINES: float = 1
    MIN_OVERLAP_RATIO: float = 0.5
    MIN_CUBE_AREA_RATIO: float = 0.01
    MAX_CUBE_AREA_RATIO: float = 0.05

    CUBES_CHANNELS: list[CubeChannelConfig] = [
        CubeChannelConfig(cv2.COLOR_BGR2HSV, 1, False),
        CubeChannelConfig(cv2.COLOR_BGR2HSV, 2, True),
        CubeChannelConfig(cv2.COLOR_BGR2HLS, 1, True),
        CubeChannelConfig(cv2.COLOR_BGR2HLS, 2, False),
        CubeChannelConfig(cv2.COLOR_BGR2LAB, 0, True),
    ]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("LookAroundBehaviour")
        self.IMG_DIR.mkdir(parents=True, exist_ok=True)

    async def run(self):
        sides: dict[SideStr, SideType] = {}
        cubes: CubesResult = CubesResult()
        for side, configs in self.ANGLES.items():
            self.logger.info(f"Looking {side}")
            results: dict[SideType, int] = {}
            for i, config in enumerate(configs):
                side_type: SideType = await self.look_and_analyse(config, side, i)
                if side_type != SideType.UNKNOWN:
                    results[side_type] = results.get(side_type, 0) + 1

                if side == "front" and i == 0:
                    cubes = self.detect_cubes(self.agent.cam.capture_array())
            self.logger.info(f"Side {side} is {side_type}")
            sorted_results: list[tuple[SideType, int]] = sorted(
                results.items(), key=lambda p: p[1], reverse=True
            )
            sides[side] = (
                sorted_results[0][0] if len(sorted_results) != 0 else SideType.UNKNOWN
            )
        res: LookAroundResponse = LookAroundResponse(**sides, cubes=cubes)
        await self.agent.look_around_handler.send_response(res)

    async def look_and_analyse(self, config: SideConfig, side: str, i: int) -> SideType:
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

        self.agent.bot.setCameraPan(config.pan)
        self.agent.bot.setCameraTilt(config.tilt)
        await asyncio.sleep(self.INTERVAL_SEC)
        img: np.ndarray = self.agent.cam.capture_array()
        cv2.imwrite(self.IMG_DIR / f"side_{side}.png", img)
        return await self.analyse(img, config.expected_angle, side, i)

    async def analyse(
        self, img: np.ndarray, expected_angle: float, side: str, i: int
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

        is_wall, segments = self.detect_plinth(img, expected_angle, side, i)
        is_open = self.detect_opening(img, expected_angle, side, segments, i)
        if is_open:
            return SideType.OPEN
        if is_wall:
            return SideType.WALL
        return SideType.UNKNOWN

    def detect_plinth(
        self, img: np.ndarray, expected_angle: float, side: str, i: int
    ) -> tuple[bool, list[Segment]]:
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
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        cv2.imwrite(self.IMG_DIR / f"thresh_{side}_{i}.png", thresh)
        linesP = cv2.HoughLinesP(
            image=thresh,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=50,
            maxLineGap=50,
        )

        with_lines = img.copy()
        count = 0
        segments: list[Segment] = []
        if linesP is not None:
            expected_vec = np.array(
                [np.cos(np.radians(expected_angle)), np.sin(np.radians(expected_angle))]
            )
            for j in range(0, len(linesP)):
                x1, y1, x2, y2 = linesP[j][0]
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
                segments.append((p1, p2))
        self.logger.debug(f"Detected {count} base wall lines")
        cv2.imwrite(self.IMG_DIR / f"lines_{side}_{i}.png", with_lines)
        return count >= self.MIN_PLINTH_LINES, segments

    def detect_opening(
        self,
        img: np.ndarray,
        expected_angle: float,
        side: str,
        plinth_segments: list[Segment],
        i: int,
    ) -> bool:
        """Detect whether there is an opening on the given side

        Args:
            img (np.ndarray): view of the side
            expected_angle (float):
                expected angle of the opening / wall (degrees, 0 to 180).
                The angle is given from the horizontal, with the Y axis going down
            side (str): name of the side, used to save debug images
            plinth_semgents (list[Segment]): list of plinth segments

        Returns:
            bool: whether an opening was detected
        """

        expected_vec = np.array(
            [np.cos(np.radians(expected_angle)), np.sin(np.radians(expected_angle))]
        )

        blurred = cv2.GaussianBlur(img, (11, 11), 5)
        lab_img = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)

        l, a, b = cv2.split(lab_img)
        l_bin = np.where(l > 150, 255, 0).astype(np.uint8)
        # _, l_bin = cv2.threshold(l, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        cv2.imwrite(self.IMG_DIR / f"{side}_l_bin_{i}.png", l_bin.astype(np.uint8))

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

            rect_area_ratio = cv2.contourArea(cnt) / area
            if rect_area_ratio < 0.7:
                continue

            total_area_ratio = area / img_area
            if total_area_ratio < 0.003 or total_area_ratio > 0.05:
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

            if not self.rect_overlaps_plinth(box, plinth_segments, l1):  # type: ignore
                continue
            cv2.drawContours(with_cnts, [box], 0, (0, 255, 0), 2)  # type: ignore
            count += 1
        self.logger.debug(f"Detected {count} opening rectangles")
        cv2.imwrite(self.IMG_DIR / f"{side}_rects_{i}.png", with_cnts)
        return count >= self.MIN_OPENING_RECTS

    def detect_cubes(self, img: np.ndarray) -> CubesResult:
        masks = []
        for i, config in enumerate(self.CUBES_CHANNELS):
            mask = self.detect_cubes_in_channel(img, config)
            cv2.imwrite(self.IMG_DIR / f"cube_mask_{i}.png", mask)
            masks.append(mask)

        mean = np.sum(np.array(masks) / 255, axis=0)
        is_cube = mean > 1

        n_strips = 3
        strips = [False] * n_strips
        strip_width = int(img.shape[1] / n_strips)
        for i in range(n_strips):
            width = (
                img.shape[1] - strip_width * (n_strips - 1)
                if i == n_strips - 1
                else strip_width
            )
            is_occupied = (
                np.mean(is_cube[:, strip_width * i : strip_width * i + width]) > 0.05
            )
            strips[i] = bool(is_occupied)

        return CubesResult(
            left=strips[0],
            front=strips[1],
            right=strips[2],
        )

    def detect_cubes_in_channel(
        self, img: np.ndarray, config: CubeChannelConfig
    ) -> np.ndarray:
        channel = cv2.split(cv2.cvtColor(img, config.space))[config.channel]
        thresh_type: int = (
            cv2.THRESH_BINARY_INV if config.inverted else cv2.THRESH_BINARY
        )
        _, thresh = cv2.threshold(channel, 0, 255, thresh_type | cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 17))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros(channel.shape, dtype=np.uint8)
        total_area = img.shape[0] * img.shape[1]
        for cnt in cnts:
            rect = cv2.minAreaRect(cnt)
            box: np.ndarray = np.intp(cv2.boxPoints(rect))  # type: ignore
            area = cv2.contourArea(box)
            area_ratio = area / total_area
            if not (self.MIN_CUBE_AREA_RATIO < area_ratio < self.MAX_CUBE_AREA_RATIO):
                continue
            cv2.drawContours(mask, [box], 0, 255, cv2.FILLED)
        return mask

    def rect_overlaps_plinth(
        self, rect: np.ndarray, segments: list[Segment], max_dist: float
    ) -> bool:
        total: int = len(segments)
        min_count: int = int(np.ceil(self.MIN_OVERLAP_RATIO * total))
        if min_count == 0:
            return True
        center: np.ndarray = np.mean(rect, axis=0)
        count: int = 0

        for segment in segments:
            d = segment[1] - segment[0]
            n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
            v = center - segment[0]
            dist = np.abs(np.dot(n, v))
            if dist < max_dist:
                count += 1
                if count >= min_count:
                    return True
        return False


class LookAroundHandler(RequestHandler):
    agent: RobotAgent

    def __init__(self, agent: RobotAgent):
        super().__init__(agent)

    async def do_request(self, req: LookAroundRequest):
        self.agent.add_behaviour(LookAroundBehaviour())
