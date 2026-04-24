from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from spade.behaviour import OneShotBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class HonkBehaviour(OneShotBehaviour):
    agent: RobotAgent

    async def run(self) -> None:
        self.agent.bot.startBuzzer()
        await asyncio.sleep(0.1)
        self.agent.bot.stopBuzzer()
        await asyncio.sleep(0.3)
        
        self.agent.bot.startBuzzer()
        await asyncio.sleep(0.1)
        self.agent.bot.stopBuzzer()
        await asyncio.sleep(0.3)
