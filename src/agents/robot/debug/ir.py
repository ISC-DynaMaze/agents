from __future__ import annotations

from typing import TYPE_CHECKING

from spade.behaviour import PeriodicBehaviour

from agents.robot.AlphaBot2 import AlphaBot2

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class IRDebugBehaviour(PeriodicBehaviour):
    agent: RobotAgent

    async def run(self) -> None:
        bot: AlphaBot2 = self.agent.bot
        left: bool = bot.getIRSensorLeft()
        right: bool = bot.getIRSensorRight()
        bot.back_leds.setBrightness(255)
        col_left = (0, 255, 0) if left else (255, 0, 0)
        col_right = (0, 255, 0) if right else (255, 0, 0)
        colors = [col_right, col_right, col_left, col_left]
        for i, col in enumerate(colors):
            bot.back_leds.setPixelColorRGB(i, *col)
        bot.back_leds.show()
