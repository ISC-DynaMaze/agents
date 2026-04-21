import asyncio
import base64
from typing import TYPE_CHECKING

import aiofiles
import cv2
from spade.behaviour import OneShotBehaviour

from common.models.camera import CameraResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.camera.agent import CameraAgent


class CapturePhotoBehaviour(OneShotBehaviour):
    agent: CameraAgent

    def __init__(self, requester_jid: str, width: int, height: int):
        super().__init__()
        self.requester_jid: str = requester_jid
        self.width: int = width
        self.height: int = height

    async def run(self):
        print("Capturing image...")
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        await asyncio.sleep(0.5)

        ret, frame = camera.read()

        if not ret:
            print("Failed to capture image.")
            return

        filename = "photo.jpg"
        cv2.imwrite(filename, frame)

        async with aiofiles.open(filename, "rb") as img_file:
            img_data = await img_file.read()
            encoded_img = base64.b64encode(img_data).decode("utf-8")

        res = CameraResponse(img=encoded_img)
        send_behaviour = BaseSenderBehaviour(res, self.requester_jid)
        self.agent.add_behaviour(send_behaviour)
