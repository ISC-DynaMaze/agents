from __future__ import annotations

from typing import TYPE_CHECKING

from spade.behaviour import PeriodicBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class FadeBehaviour(PeriodicBehaviour):
    agent: RobotAgent

    async def on_start(self) -> None:
        self.brightness = 0
        self.dir = 1
        self.leds = self.agent.bot.back_leds
        self.n_leds: int = self.leds.numPixels()
        self.leds.setBrightness(0)
        for i in range(self.n_leds):
            self.leds.setPixelColorRGB(i, 255, 255, 255)
        self.leds.show()

    async def run(self):
        self.leds.setBrightness(self.brightness)
        self.leds.show()
        self.brightness += self.dir

        if self.brightness >= 255 or self.brightness <= 0:
            self.dir *= -1
