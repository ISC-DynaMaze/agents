import asyncio
import datetime
from asyncio import Event, Lock
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import numpy as np
from spade.agent import Agent

from common.models.camera import CameraRequest, CameraResponse
from common.sender import BaseSenderBehaviour


class CameraManager:
    VALIDITY_SEC: float = 0.5
    TIMEOUT: float = 2

    def __init__(self, agent: Agent, camera_jid: str) -> None:
        self.agent: Agent = agent
        self.camera_jid: str = camera_jid

        self.last_image: Optional[np.ndarray] = None
        self.last_path: Optional[Path] = None
        self.last_received_at: datetime.datetime = datetime.datetime.now()
        self.tmp_dir: TemporaryDirectory = TemporaryDirectory(prefix="dynamaze_cam")
        self.save_dir: Path = Path(self.tmp_dir.name)

        self._request_lock: Lock = Lock()
        self._received_event: Event = Event()

    def cleanup(self):
        self.tmp_dir.cleanup()

    async def get_img(self) -> Optional[np.ndarray]:
        await self._check_request()
        return self.last_image

    async def get_path(self) -> Optional[Path]:
        await self._check_request()
        return self.last_path

    async def _check_request(self):
        now: datetime.datetime = datetime.datetime.now()
        delta: float = (now - self.last_received_at).total_seconds()
        if self.last_image is None or delta > self.VALIDITY_SEC:
            await self._request()

    async def _request(self):
        async with self._request_lock:
            req: CameraRequest = CameraRequest()
            self.agent.add_behaviour(BaseSenderBehaviour(req, self.camera_jid))
            self._received_event.clear()
            try:
                await asyncio.wait_for(self._received_event.wait(), timeout=self.TIMEOUT)
            except asyncio.TimeoutError:
                return
            return self.last_image

    async def on_receive(self, res: CameraResponse):
        self.last_image, self.last_path = await res.decode_img(self.save_dir)
        self.last_received_at = datetime.datetime.now()
        self._received_event.set()
