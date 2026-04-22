import logging
from pathlib import Path

from spade.agent import Agent

from agents.controller.photo import ReceivePhotoBehaviour, RequestPhotoBehaviour

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Enable SPADE and XMPP specific logging
for log_name in ["spade", "aioxmpp", "xmpp"]:
    log = logging.getLogger(log_name)
    log.setLevel(logging.DEBUG)
    log.propagate = True


class ControllerAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("ControllerAgent")

    async def setup(self):
        ask_photo = RequestPhotoBehaviour("camera_agent@isc-coordinator.lan")

        # ReceivePhotoBehaviour will save the photo, run bot detection, build maze and send maze data to requester
        receive_photo = ReceivePhotoBehaviour(
            save_dir=Path("photos"),
            maze_dir=Path("mazes"),
            request_jid="receiver_agent@isc-coordinator.lan",
        )

        self.add_behaviour(ask_photo)
        self.add_behaviour(receive_photo)
