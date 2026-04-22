from __future__ import annotations

import base64
import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import cv2
import numpy as np

from agents.controller.bot_detection import BotDetectionBehaviour
from agents.controller.build_maze import BuildMazeBehaviour
from common.models.camera import CameraResponse
from common.models.common import Response
from common.receiver import BaseReceiverBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class ReceiverBehaviour(BaseReceiverBehaviour):
    agent: ControllerAgent

    def __init__(self, save_dir: Path, maze_dir: Path, requester_jid: str):
        super().__init__()
        self.save_dir: Path = save_dir
        self.maze_dir: Path = maze_dir
        self.requester_jid: str = requester_jid

    async def on_start(self) -> None:
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.maze_dir.mkdir(parents=True, exist_ok=True)
        return await super().on_start()

    async def on_response(self, res: Response):
        match res:
            case CameraResponse(img=encoded_img):
                print("Received photo message.")
                img_data = base64.b64decode(encoded_img)

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
                    request_jid=self.requester_jid,
                    output_dir=self.maze_dir,
                )
                self.agent.add_behaviour(build_maze)
