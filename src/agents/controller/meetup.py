from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np
from spade.behaviour import PeriodicBehaviour

from agents.controller.bot_detection import BotDetector

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class MeetupBehaviour(PeriodicBehaviour):
    agent: ControllerAgent

    MIN_DISTANCE: float = 100
    NEXT_DISTANCE: float = 32

    def __init__(self, period: float, start_at: datetime | None = None, debug: bool = False):
        super().__init__(period, start_at)
        self.logger = logging.getLogger("MeetupBehaviour")
        self.debug: bool = debug

    async def run(self):
        too_close: list[tuple[float, float]] = await self.check_too_close()
        if self.agent.maze is None:
            return
        self.agent.maze.clear_occupied()
        if len(too_close) != 0:
            self.logger.info(f"Robot is close to someone else: {too_close}")
            for px, py in too_close:
                row, col = self.agent.maze.pixel_to_cell(px, py)
                self.agent.maze.mark_occupied(row, col)

    async def check_too_close(self) -> list[tuple[float, float]]:
        img: Optional[np.ndarray] = await self.agent.camera.get_img()
        if img is None:
            self.logger.error("Could not get image from camera")
            return []
        detector: BotDetector = BotDetector(img)
        bot_pos: dict[int, tuple[float, float]] = detector.get_positions()
        bot_angles: dict[int, float] = detector.get_angles()
        self_id: int = self.agent.config.bot_aruco_id
        if self_id not in bot_pos:
            self.logger.error("Robot not detected")
            return []

        if len(bot_pos) == 1:
            self.logger.warning("No other robot detected")
            return []

        bot_next_pos: dict[int, np.ndarray] = self._compute_next_pos(
            bot_pos, bot_angles
        )
        self_next_pos: np.ndarray = bot_next_pos[self_id]

        debug_img: np.ndarray = img.copy()
        too_close: list[tuple[float, float]] = []
        for bot_id, next_pos in bot_next_pos.items():
            if self.debug:
                p1 = np.array(bot_pos[bot_id]).astype(np.uint32)
                p2 = np.array(next_pos).astype(np.uint32)
                cv2.line(debug_img, p1, p2, (0, 0, 0), 2)
                cv2.circle(debug_img, p1, 5, (0, 0, 255), -1)
                cv2.circle(debug_img, p2, 5, (0, 255, 0), -1)
            if bot_id == self_id:
                continue
            dist: float = self._compute_distance(self_next_pos, next_pos)
            if dist <= self.MIN_DISTANCE:
                too_close.append(bot_pos[bot_id])
        if self.debug:
            cv2.imwrite("debug_meetup.png", debug_img)
        return too_close

    def _compute_next_pos(
        self, positions: dict[int, tuple[float, float]], angles: dict[int, float]
    ) -> dict[int, np.ndarray]:
        next_positions: dict[int, np.ndarray] = {}
        for bot_id, pos in positions.items():
            angle = np.radians(angles[bot_id])
            direction: np.ndarray = np.array([np.cos(angle), np.sin(angle)])
            next_pos: np.ndarray = np.array(pos) + self.NEXT_DISTANCE * direction
            next_positions[bot_id] = next_pos
        return next_positions

    def _compute_distance(self, pos1: np.ndarray, pos2: np.ndarray) -> float:
        return float(np.linalg.norm(pos2 - pos1))
