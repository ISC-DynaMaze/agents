from __future__ import annotations

import asyncio
import datetime
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from common.models.common import ReqResAdapter
from common.models.controller import AngleRequest, AngleResponse
from common.models.robot import Direction
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class AngleCalibrationBehaviour(OneShotBehaviour):
    agent: RobotAgent

    def __init__(self, time=0.1, speed=20, delta_t=0.05):
        super().__init__()
        self.actual_angle = None
        self.speed = speed
        self.time = time
        self.delta_t = delta_t
        self.logger = logging.getLogger("AngleCalibrationBehaviour")

    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot

    async def run(self):
        await self.calibrate_direction(Direction.Left)
        await self.calibrate_direction(Direction.Right)

    async def ask_angle(self):
        self.logger.debug("[Behaviour] Ask controller for actual angle")

        msg = AngleRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(msg, self.agent.controller_jid))

        while True:
            reply = await self.receive(timeout=15)
            try:
                assert reply is not None
                res = ReqResAdapter.validate_json(reply.body)
                assert isinstance(res, AngleResponse)
                break
            except:
                continue
        return res.angle

    async def calibrate_direction(self, direction: Direction):
        self.actual_angle = await self.ask_angle()
        if self.actual_angle is None:
            self.logger.info("[Behaviour] No angle given")
            return
        self.bot.setBothPWM(self.speed)
        angle_history = [self.actual_angle]
        delta_history = []
        for i in range(10):
            await self.calibration_sequence(
                angle_history, delta_history, i * self.delta_t, direction
            )
        self.logger.info(f"[Calibration result] : {delta_history}")
        test = self.interpolate(delta_history)

        self.logger.info(f"[Interpolate] : {test}")
        result_test = await self.test_sequence(test, direction)
        self.save_result(delta_history, result_test, direction)

    async def calibration_sequence(
        self,
        angle_history: list[float],
        delta_history: list[list[float]],
        delta_t: float,
        direction: Direction,
    ):
        timing = self.time + delta_t
        self.logger.info(f"[Behaviour] Robot turn left for {timing} second(s)")

        if direction == Direction.Left:
            self.bot.left()
        elif direction == Direction.Right:
            self.bot.right()
        await asyncio.sleep(timing)
        self.bot.stop()
        await asyncio.sleep(1)
        self.actual_angle = await self.ask_angle()
        angle_history.append(self.actual_angle)
        delta = abs(((angle_history[-2] - angle_history[-1] + 180) % 360) - 180)
        self.logger.info(f"[Time] Time saved : {timing}")
        delta_history.append([delta, timing])

    def interpolate(self, delta_history: list[list[float]]) -> list[float]:
        x = []
        y = []
        for c in delta_history:
            x.append(c[0])
            y.append(c[1])
        print(x)
        print(y)
        return np.interp([45, 90, 135], x, y)

    async def test_sequence(
        self, test: list[float], direction: Direction
    ) -> list[dict]:
        test_angle_history = []
        test_delta_history = []
        targets = [45, 90, 135]  # Validation test

        for i, t in enumerate(test):
            start_angle = await self.ask_angle()
            test_angle_history.append(start_angle)

            if direction == Direction.Left:
                self.bot.left()
            else:
                self.bot.right()
            await asyncio.sleep(t)
            self.bot.stop()

            await asyncio.sleep(1.5)
            end_angle = await self.ask_angle()
            test_angle_history.append(end_angle)

            delta = abs(((start_angle - end_angle + 180) % 360) - 180)

            test_delta_history.append(
                {"target": targets[i], "time": float(t), "obtained": float(delta)}
            )

        self.bot.stop()
        return test_delta_history

    def save_result(
        self,
        delta_history: list[list[float]],
        test_delta_history: list[dict],
        direction: Direction,
    ):
        data = {
            "speed": self.speed,
            "measures": [
                {"angle": float(d[0]), "time": float(d[1])} for d in delta_history
            ],
            "tests": test_delta_history,
        }

        save_path = Path(f"test_result_{direction}")
        save_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = save_path / f"debug_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Results saved in {filename}")
        except Exception as e:
            self.logger.error(f"Error :  {e}")

    def load_latest_data(self, direction: Direction):
        files = list(Path(f"test_result_{direction}").glob("debug_*.json"))
        if not files:
            raise ValueError("No file founded")

        latest_file = sorted(files)[-1]

        parts = latest_file.stem.split("_")
        date_str = f"{parts[1]}_{parts[2]}"
        file_time = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        return latest_file, file_time
