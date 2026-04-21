from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

from spade.behaviour import CyclicBehaviour

if TYPE_CHECKING:
    from agents.logger.logger import LoggerAgent


class MessageReceiverBehaviour(CyclicBehaviour):
    agent: LoggerAgent

    async def run(self) -> None:
        msg = await self.receive(timeout=9999)
        if msg is not None and msg.body is not None:
            try:
                data = json.loads(msg.body)
                await self.process_message(data)
            except json.JSONDecodeError:
                return

    async def process_message(self, msg: dict):
        msg_type: Optional[str] = msg.get("type")
        if msg_type is None:
            return

        await self.agent.send_ws({"type": "msg", "msg": msg})

        match msg_type:
            case "bot-img":
                await self.agent.send_ws({"type": "bot-img", "img": msg["img"]})
