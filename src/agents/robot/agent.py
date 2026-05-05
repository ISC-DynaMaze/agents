from __future__ import annotations

import logging
from dataclasses import dataclass

from picamera2 import Picamera2
from spade.agent import Agent

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.leds_manager import LedsManager
from agents.robot.look_around import LookAroundHandler
from agents.robot.receiver import ReceiverBehaviour
from agents.robot.status import StatusBehaviour
from common.log_mixin import LogMixin


@dataclass
class WheelAdjustments:
    balance: float = 0  # turn right: >0 | turn left: <0

    def more_right(self):
        self.balance += 0.02

    def more_left(self):
        self.balance -= 0.02

    @property
    def left_factor(self) -> float:
        return 1 + self.balance

    @property
    def right_factor(self) -> float:
        return 1 - self.balance


class RobotAgent(Agent, LogMixin):
    bot: AlphaBot2
    cam: Picamera2
    leds: LedsManager

    def __init__(
        self,
        *args,
        logger_jid: str = "logger@isc-coordinator.lan",
        controller_jid: str = "alberto-ctrl@isc-coordinator.lan",
        camera_res: tuple[int, int] = (720, 540),
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.logger_jid: str = logger_jid
        self.controller_jid: str = controller_jid
        self.camera_res: tuple[int, int] = camera_res
        self.logger = logging.getLogger("RobotAgent")

        self.set_logger_jid(self.logger_jid)
        self.set_sender(str(self.jid))

        self.look_around_handler: LookAroundHandler = LookAroundHandler(self)

        self.wheel_adjustements: WheelAdjustments = WheelAdjustments()

    async def setup(self):
        self.bot = AlphaBot2()
        self.cam = Picamera2()
        self.leds = LedsManager(self.bot)

        config = self.cam.create_preview_configuration(
            main={"format": "RGB888", "size": self.camera_res}
        )
        self.cam.configure(config)
        self.cam.start()

        receiver_behaviour = ReceiverBehaviour()
        self.add_behaviour(receiver_behaviour)

        status_behaviour = StatusBehaviour(self.logger_jid, 10)
        self.add_behaviour(status_behaviour)

    async def stop(self) -> None:
        self.cam.stop()
        self.bot.disableCameraPan()
        self.bot.disableCameraTilt()
        self.bot.stop()
        self.leds.off()
        self.leds.show()
        self.bot.stopBuzzer()
        return await super().stop()
