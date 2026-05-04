import logging
from pathlib import Path

from spade.agent import Agent

from agents.controller.receiver import ReceiverBehaviour
from common.config import Config
from common.log_mixin import LogMixin


class ControllerAgent(Agent, LogMixin):
    def __init__(self, *args, camera_jid: str, logger_jid: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("ControllerAgent")
        self.camera_jid: str = camera_jid
        self.logger_jid: str = logger_jid

        self.set_logger_jid(self.logger_jid)
        self.set_sender(str(self.jid))

        self.config: Config = Config.load()

        self.maze = None
        self.grid_img = None
        self.current_path = None

        self.maze_requesters: list[str] = []
        self.angle_requesters: list[str] = []
        self.path_requesters: list[str] = []
        self.direction_requesters: list[str] = []
        self.obstacles_requesters: list[str] = []
        self.cubes_requesters: list[str] = []
        self.requesting_image: bool = False
        self.requesting_direction: bool = False
        self.requesting_obstacles: bool = False
        self.requesting_cubes: bool = False

    async def setup(self):
        receiver_behaviour = ReceiverBehaviour(
            save_dir=Path("photos"),
            maze_dir=Path("mazes"),
            path_dir=Path("paths"),
            obstacles_dir=Path("obstacles"),
            cubes_dir=Path("cubes"),
        )
        self.add_behaviour(receiver_behaviour)
