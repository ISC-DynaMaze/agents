import asyncio
import datetime
import json
import logging
from pathlib import Path
import numpy as np
from spade.behaviour import OneShotBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from common.models.common import ReqResAdapter
from common.models.controller import AngleRequest, AngleResponse
from common.sender import BaseSenderBehaviour


class AngleCalibrationBehaviour(OneShotBehaviour):
    def __init__(self, time, speed=20, delta_t=0.05, calib_threshold=60):
        super().__init__()
        self.actual_angle = None
        self.speed = speed
        self.time = time
        self.delta_t = delta_t
        self.calib_threshold = calib_threshold
        self.logger = logging.getLogger("AngleCalibrationBehaviour")

    async def on_start(self):
        self.bot: AlphaBot2 = self.agent.bot

    async def run(self):
        new_calibration = True
        latest_data = self.load_latest_data()
        self.logger.info(f"[File date] : {latest_data}")

        if latest_data:
            now = datetime.datetime.now()
            interval = (now - latest_data[1]).total_seconds()
            if interval > 3600:
                self.logger.info("[Behaviour] New calibration required")

            else:
                self.logger.info("[Behaviour] No need of new calibration")
                new_calibration = False
        else:
            self.logger.info("[Behaviour] No existing calibration")
            new_calibration = True

        if new_calibration:
            self.actual_angle = await self.ask_angle()
            if self.actual_angle is None:
                self.logger.info(f"[Behaviour] No angle given")
                return
            self.bot.setBothPWM(self.speed)
            angle_history = [self.actual_angle]
            delta_history = []
            await self.calibration_sequence(angle_history, delta_history)
            for i in range(7):
                await self.calibration_sequence(
                    angle_history, delta_history, self.delta_t
                )
            self.logger.info(f"[Calibration result] : {delta_history}")
            test = self.interpolate(delta_history)

            self.logger.info(f"[Interpolate] : {test}")
            result_test = await self.test_sequence(test)
            self.save_result(delta_history, result_test)
        else:
            self.load_profile(latest_data[0])

    async def ask_angle(self):
        self.logger.debug("[Behaviour] Ask controller for actual angle")

        msg = AngleRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(msg, "camera@isc-coordinator.lan"))

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

    async def calibration_sequence(self, angle_history, delta_history, delta_t=0.1):
        self.logger.info(f"[Time] Time : {self.time}")
        self.logger.info(f"[Time] Additional time : {delta_t}")
        self.logger.info(f"[Behaviour] Robot turn left for {self.time+delta_t} second(s)")
        self.bot.left()
        await asyncio.sleep(self.time + delta_t)
        self.time += delta_t
        self.bot.stop()
        await asyncio.sleep(1)
        self.logger.info("[Behaviour] Robot Stop")
        self.actual_angle = await self.ask_angle()
        angle_history.append(self.actual_angle)
        delta = abs(((angle_history[-2] - angle_history[-1] + 180) % 360) - 180)
        delta_history.append([delta, self.time])

    def interpolate(self, delta_history):
        x = []
        y = []
        for c in delta_history:
            x.append(c[0])
            y.append(c[1])
        print(x)
        print(y)
        return np.interp([45, 90, 135], x, y)

    async def test_sequence(self, test):
        test_angle_history = []
        test_delta_history = []
        targets = [45, 90, 135]  # Pour référence

        for i, t in enumerate(test):
            start_angle = await self.ask_angle()
            test_angle_history.append(start_angle)

            self.bot.left()
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

    def save_result(self, delta_history, test_delta_history):
        data = {
            "speed": self.speed,
            "measures": [
                {"angle": float(d[0]), "time": float(d[1])} for d in delta_history
            ],
            "tests": test_delta_history,
        }

        save_path = Path("test_result")
        save_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = save_path / f"debug_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Results saved in {filename}")
        except Exception as e:
            self.logger.error(f"Error :  {e}")

    def load_latest_data(self):
        files = list(Path("test_result").glob("debug_*.json"))
        if not files:
            return False

        latest_file = sorted(files)[-1]

        parts = latest_file.stem.split("_")
        date_str = f"{parts[1]}_{parts[2]}"
        file_time = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        return latest_file, file_time

    def load_profile(self, file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                self.delta_history = [[m["angle"], m["time"]] for m in data["measures"]]
                self.speed = data.get("speed", 20)
                self.logger.info(f"[Load] Existing config loaded ")
                return True
        except Exception as e:
            self.logger.error(f"[Load] Erreur : {e}")
            return False
