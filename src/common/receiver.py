import logging

from pydantic import ValidationError
from spade.behaviour import CyclicBehaviour

from models.base import RequestBase, ResponseBase
from models.common import ReqRes, ReqResAdapter, Request, Response


class ReceiverBehaviour(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("ReceiverBehaviour")

    async def run(self):
        msg = await self.receive(timeout=9999)
        if msg is not None and msg.body is not None:
            await self.process_message(msg.body)

    async def process_message(self, msg: str):
        try:
            req_res: ReqRes = ReqResAdapter.validate_json(msg)
            match req_res:
                case RequestBase() as req:
                    await self.on_request(req) # type: ignore
                case ResponseBase() as res:
                    await self.on_response(res) # type: ignore
        except ValidationError as e:
            self.logger.warning(f"Ignoring malformed request: {e}")

    async def on_request(self, req: Request):
        pass

    async def on_response(self, req: Response):
        pass
