from __future__ import annotations

from typing import TYPE_CHECKING

from spade.behaviour import PeriodicBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class DiscoBehaviour(PeriodicBehaviour):
    agent: RobotAgent

    async def on_start(self) -> None:
        self.idx = 0
        self.dir = 1
        self.leds = self.agent.bot.back_leds
        self.n_leds: int = self.leds.numPixels()

    async def run(self):
        for i in range(self.n_leds):
            is_on: bool = i == self.idx
            self.leds.setBrightness(255 if is_on else 0)
        self.leds.show()
        self.idx += self.dir

        if self.idx >= self.n_leds - 1 or self.idx <= 0:
            self.dir *= -1
