import logging

from pydantic import ValidationError
from spade.behaviour import CyclicBehaviour

from common.models.base import RequestBase, ResponseBase
from common.models.common import ReqRes, ReqResAdapter, Request, Response


class BaseReceiverBehaviour(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("BaseReceiverBehaviour")

    async def run(self):
        msg = await self.receive(timeout=9999)
        if msg is not None and msg.body is not None:
            await self.process_message(str(msg.sender), msg.body)

    async def process_message(self, sender_jid: str, msg: str):
        try:
            req_res: ReqRes = ReqResAdapter.validate_json(msg)
            match req_res:
                case RequestBase() as req:
                    await self.on_request(sender_jid, req)  # type: ignore
                case ResponseBase() as res:
                    await self.on_response(sender_jid, res)  # type: ignore
        except ValidationError:
            await self.on_raw(sender_jid, msg)

    async def on_request(self, sender_jid: str, req: Request):
        pass

    async def on_response(self, sender_jid: str, res: Response):
        pass

    async def on_raw(self, sender_jid: str, msg: str):
        pass
