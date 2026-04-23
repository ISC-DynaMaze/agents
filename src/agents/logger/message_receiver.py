from __future__ import annotations

from typing import TYPE_CHECKING

from common.models.common import Request, Response
from common.models.logger import LogRequest
from common.models.robot import CameraPhotoResponse, StatusResponse
from common.receiver import BaseReceiverBehaviour

if TYPE_CHECKING:
    from agents.logger.logger import LoggerAgent


class MessageReceiverBehaviour(BaseReceiverBehaviour):
    agent: LoggerAgent

    async def on_request(self, sender_jid: str, req: Request):
        match req:
            case LogRequest(sender=sender, msg=msg, log_type=log_type):
                await self.agent.send_ws({
                    "type": "msg",
                    "sender": sender,
                    "msg": msg,
                    "log_type": log_type
                })

    async def on_response(self, sender_jid: str, res: Response):
        match res:
            case CameraPhotoResponse(img=img):
                await self.agent.send_ws({
                    "type": "bot-img",
                    "img": img
                })
            
            case StatusResponse(camera=cam_status):
                await self.agent.send_ws({
                    "type": "cam-status",
                    "status": cam_status.model_dump()
                })
