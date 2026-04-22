import logging
from pathlib import Path

from spade.agent import Agent

from agents.controller.receiver import ReceiverBehaviour

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Enable SPADE and XMPP specific logging
for log_name in ["spade", "aioxmpp", "xmpp"]:
    log = logging.getLogger(log_name)
    log.setLevel(logging.DEBUG)
    log.propagate = True


class ControllerAgent(Agent):
    def __init__(self, *args, camera_jid: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("ControllerAgent")
        self.camera_jid: str = camera_jid

        self.maze_requesters: list[str] = []

    async def setup(self):
        receiver_behaviour = ReceiverBehaviour(
            save_dir=Path("photos"),
            maze_dir=Path("mazes"),
        )
        self.add_behaviour(receiver_behaviour)
