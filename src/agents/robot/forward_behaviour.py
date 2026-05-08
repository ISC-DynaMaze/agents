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
        self.bot.setPWMA(self.speed * self.agent.wheel_adjustements.left_factor)
        self.bot.setPWMB(self.speed * self.agent.wheel_adjustements.right_factor)

        await asyncio.sleep(0.05)
