from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from spade.behaviour import CyclicBehaviour

from agents.robot.AlphaBot2 import AlphaBot2

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class ForwardBehaviour(CyclicBehaviour):
    agent: RobotAgent

    def __init__(self, speed: int = 20):
        super().__init__()
        self.speed: int = speed

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def run(self) -> None:
        left_free: bool = self.bot.getIRSensorLeft()
        right_free: bool = self.bot.getIRSensorRight()

        speed_left: int = self.speed
        speed_right: int = self.speed

        sides: tuple[bool, bool] = (left_free, right_free)

        match sides:
            case (False, False):
                speed_left = 0
                speed_right = 0

            case (False, True):
                speed_right = 0

            case (True, False):
                speed_left = 0

        if speed_left == 0 and speed_right == 0:
            self.bot.stop()
        else:
            self.bot.setPWMA(speed_left * self.agent.wheel_adjustements.left_factor)
            self.bot.setPWMB(speed_right * self.agent.wheel_adjustements.right_factor)

        await asyncio.sleep(0.05)
