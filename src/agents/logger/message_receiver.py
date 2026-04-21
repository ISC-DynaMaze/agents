from __future__ import annotations

import json
from typing import TYPE_CHECKING

from common.models.common import Response
from common.models.logger import LogRequest
from common.models.robot import CameraPhotoResponse
from common.receiver import BaseReceiverBehaviour

if TYPE_CHECKING:
    from agents.logger.logger import LoggerAgent


class MessageReceiverBehaviour(BaseReceiverBehaviour):
    agent: LoggerAgent

    async def on_response(self, res: Response):
        match res:
            case LogRequest(sender=sender, msg=msg, log_type=log_type):
                await self.agent.send_ws({
                    "type": "msg",
                    "sender": sender,
                    "msg": msg,
                    "log_type": log_type
                })
            
            case CameraPhotoResponse(img=img):
                await self.agent.send_ws({
                    "type": "bot-img",
                    "bot-img": img
                })
