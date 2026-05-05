from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from agents.robot.leds_manager import State

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class PenaltyHandler:
    BPM: float = 180
    SAD_NOISES_RHYTHM: list[float] = [0.5, 1, 0.5, 2 / 3, 2 / 3, 2 / 3, 1, 1, 1]

    def __init__(self, agent: RobotAgent) -> None:
        self.agent: RobotAgent = agent
        self._duration: float = 0

    async def sad_noises(self):
        quarter_sec: float = 60 / self.BPM

        for note in self.SAD_NOISES_RHYTHM:
            duration: float = note * quarter_sec
            on_time: float = 0.9 * duration
            off_time = duration - on_time
            self.agent.bot.startBuzzer()
            await asyncio.sleep(on_time)
            self.agent.bot.stopBuzzer()
            await asyncio.sleep(off_time)

    async def pause_point(self):
        if self._duration != 0:
            await self.sit_out()
            self._duration = 0

    async def sit_out(self):
        self.agent.leds.stash()
        self.agent.leds.set_state(State.PENALTY)

        t0 = time.monotonic()
        await self.sad_noises()
        t1 = time.monotonic()
        remaining: float = self._duration - (t1 - t0)
        await asyncio.sleep(max(0, remaining))

        self.agent.leds.pop()

    def add(self, duration: float):
        self._duration += duration
