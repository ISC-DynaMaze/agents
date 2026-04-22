import base64
import datetime
from pathlib import Path

import aiofiles
import cv2
import numpy as np
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

from agents.controller.bot_detection import BotDetectionBehaviour
from agents.controller.build_maze import BuildMazeBehaviour
from common.models.camera import CameraRequest
from common.sender import BaseSenderBehaviour


class RequestPhotoBehaviour(OneShotBehaviour):
    agent: Agent

    def __init__(self, camera_jid: str):
        super().__init__()
        self.camera_jid: str = camera_jid

    async def run(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, self.camera_jid))


class ReceivePhotoBehaviour(CyclicBehaviour):
    agent: Agent

    def __init__(self, save_dir: Path, maze_dir: Path, request_jid: str):
        super().__init__()
        self.save_dir: Path = save_dir
        self.maze_dir: Path = maze_dir
        self.request_jid: str = request_jid

        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.maze_dir.mkdir(parents=True, exist_ok=True)

    async def run(self):
        print("Waiting for photo message...")
        msg = await self.receive(timeout=9999)
        if msg is not None and msg.body is not None:
            print("Received photo message.")
            img_data = base64.b64decode(msg.body)

            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            filepath = self.save_dir / filename

            # Save the received image
            async with aiofiles.open(filepath, "wb") as img_file:
                await img_file.write(img_data)

            print(f"Photo saved as '{filepath}'.")
            img: np.ndarray = cv2.imread(filepath)  # type: ignore
            bot_detection = BotDetectionBehaviour(img)
            self.agent.add_behaviour(bot_detection)

            build_maze = BuildMazeBehaviour(
                photo_path=filepath,
                request_jid=self.request_jid,
                output_dir=self.maze_dir,
            )
            self.agent.add_behaviour(build_maze)
