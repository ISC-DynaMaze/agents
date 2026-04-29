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
        self.slow_speed: int = int(round(self.speed * 0.8))

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
                speed_right = self.slow_speed

            case (True, False):
                speed_left = self.slow_speed

        if speed_left == 0 and speed_right == 0:
            self.bot.stop()
        else:
            self.bot.setPWMA(speed_right)
            self.bot.setPWMB(speed_left)

        await asyncio.sleep(0.05)
