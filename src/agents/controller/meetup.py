from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import numpy as np
from spade.behaviour import PeriodicBehaviour

from agents.controller.bot_detection import BotDetector

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class MeetupBehaviour(PeriodicBehaviour):
    agent: ControllerAgent

    MIN_DISTANCE: float = 32
    NEXT_DISTANCE: float = 32

    def __init__(self, period: float, start_at: datetime | None = None):
        super().__init__(period, start_at)
        self.logger = logging.getLogger("MeetupBehaviour")

    async def run(self):
        too_close: bool = await self.check_too_close()
        if too_close:
            self.logger.info("Robot is close to someone else")

    async def check_too_close(self) -> bool:
        img: Optional[np.ndarray] = await self.agent.camera.get_img()
        if img is None:
            self.logger.error("Could not get image from camera")
            return False
        detector: BotDetector = BotDetector(img)
        bot_pos: dict[int, tuple[float, float]] = detector.get_positions()
        bot_angles: dict[int, float] = detector.get_angles()
        self_id: int = self.agent.config.bot_aruco_id
        if self_id not in bot_pos:
            self.logger.error("Robot not detected")
            return False

        if len(bot_pos) == 1:
            self.logger.warning("No other robot detected")
            return False

        bot_next_pos: dict[int, np.ndarray] = self._compute_next_pos(
            bot_pos, bot_angles
        )
        self_next_pos: np.ndarray = bot_next_pos[self_id]

        for bot_id, next_pos in bot_next_pos.items():
            if bot_id == self_id:
                continue
            dist: float = self._compute_distance(self_next_pos, next_pos)
            if dist <= self.MIN_DISTANCE:
                return True
        return False

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
