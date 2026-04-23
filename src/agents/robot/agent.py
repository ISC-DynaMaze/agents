from __future__ import annotations

import logging

from picamera2 import Picamera2
from spade.agent import Agent

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.receiver import ReceiverBehaviour
from agents.robot.status import StatusBehaviour

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("AlphaBotAgent")

# Enable SPADE and XMPP specific logging
for log_name in ["spade", "aioxmpp", "xmpp"]:
    log = logging.getLogger(log_name)
    log.setLevel(logging.DEBUG)
    log.propagate = True


class RobotAgent(Agent):
    bot: AlphaBot2
    cam: Picamera2

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

    async def setup(self):
        self.bot = AlphaBot2()
        self.cam = Picamera2()

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
        return await super().stop()
