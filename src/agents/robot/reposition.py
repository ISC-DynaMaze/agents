from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.turn import TurningBehaviour
from common.models.common import ReqResAdapter
from common.models.controller import AngleRequest, AngleResponse
from common.models.robot import Direction
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class RepositionBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, tolerance_deg: float = 2):
        super().__init__()
        self.logger = logging.getLogger("RepositionBehaviour")
        self.tolerance_deg = tolerance_deg

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    @property
    def bot_id(self) -> int:
        return self.agent.config.bot_aruco_id

    async def run(self):
        self.bot.stop()

        # get angle
        await self.ask_angle()
        current_angle: Optional[float] = await self.wait_angle_response(timeout=5)
        if current_angle is None:
            self.logger.error("Cannot reposition because current angle is none")
            return
        await self.reposition_to_nearest_90_degree(current_angle)

    async def wait_angle_response(self, timeout) -> Optional[float]:
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error(
                        "Timed out waiting for direction response message"
                    )
                    return None
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, AngleResponse)
                return res.angles.get(self.bot_id)
            except Exception as e:
                self.logger.error(f"Error occurred while waiting for angle: {e}")
                continue

    async def ask_angle(self):
        req = AngleRequest()
        self.agent.add_behaviour(
            BaseSenderBehaviour(req, str(self.agent.controller_jid))
        )

    async def reposition_to_nearest_90_degree(self, current_angle: float):
        # normalize to [0, 360) to make nearest cardinal computation robust
        current_angle %= 360
        nearest_90 = round(current_angle / 90) * 90

        # signed shortest-angle difference in (-180, 180]
        angle_diff = (nearest_90 - current_angle + 180) % 360 - 180

        if abs(angle_diff) <= self.tolerance_deg:
            self.logger.info(
                f"Already aligned: current={current_angle:.2f}°, target={nearest_90:.2f}°, diff={angle_diff:.2f}°"
            )
            return

        direction = Direction.Right if angle_diff > 0 else Direction.Left
        correction_angle = abs(angle_diff)
        if direction == Direction.Right:
            self.agent.wheel_adjustements.more_right()
        else:
            self.agent.wheel_adjustements.more_left()

        self.logger.info(
            f"Repositioning to nearest 90°: current={current_angle:.2f}°, target={nearest_90:.2f}°, correction={correction_angle:.2f}° {direction.value}"
        )

        behaviour = TurningBehaviour(direction=direction, angle=correction_angle)
        self.agent.add_behaviour(behaviour)
        await behaviour.join()
