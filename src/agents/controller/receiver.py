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
from agents.controller.photo import RequestPhotoBehaviour
from agents.controller.find_path import FindPathBehaviour
from common.models.camera import CameraResponse
from common.models.common import Request, Response
from common.models.controller import AngleRequest, MazeRequest, PathRequest, PathResponse
from common.receiver import BaseReceiverBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class ReceiverBehaviour(BaseReceiverBehaviour):
    agent: ControllerAgent

    def __init__(self, save_dir: Path, maze_dir: Path):
        super().__init__()
        self.save_dir: Path = save_dir
        self.maze_dir: Path = maze_dir

    async def on_start(self) -> None:
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.maze_dir.mkdir(parents=True, exist_ok=True)
        return await super().on_start()

    async def request_photo(self):
        ask_photo = RequestPhotoBehaviour(self.agent.camera_jid)
        self.agent.add_behaviour(ask_photo)

    async def on_request(self, sender_jid: str, req: Request):
        match req:
            case MazeRequest():
                self.agent.maze_requesters.append(sender_jid)
                if not self.agent.requesting_image:
                    await self.request_photo()
            
            case AngleRequest():
                self.agent.angle_requesters.append(sender_jid)
                if not self.agent.requesting_image:
                    await self.request_photo()
            
            case PathRequest():
                self.agent.path_requesters.append(sender_jid)
                if not self.agent.maze:
                    self.agent.logger.error("Received path request but maze is not set")
                    return

    async def on_response(self, sender_jid: str, res: Response):
        match res:
            case CameraResponse(img=encoded_img):
                self.agent.requesting_image = False

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

                if len(self.agent.angle_requesters) != 0:
                    bot_detection = BotDetectionBehaviour(img)
                    self.agent.add_behaviour(bot_detection)

                if len(self.agent.maze_requesters) != 0:
                    build_maze = BuildMazeBehaviour(
                        photo_path=filepath,
                        output_dir=self.maze_dir,
                    )
                    self.agent.add_behaviour(build_maze)
                
                if len(self.agent.path_requesters) != 0:
                    find_path = FindPathBehaviour(maze=self.agent.maze)  # type: ignore
                    self.agent.add_behaviour(find_path)

            case PathResponse(path=path):
                print("Received path response")
                print(f"Path: {path}")
                self.agent.current_path = path
