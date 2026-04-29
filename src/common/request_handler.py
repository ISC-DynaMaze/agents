from spade.agent import Agent

from common.models.base import Base
from common.sender import MultiSenderBehaviour


class RequestHandler:
    def __init__(self, agent: Agent):
        self.agent: Agent = agent
        self.requesters: list[str] = []
        self.requesting: bool = False

    async def on_request(self, requester: str, req: Base):
        self.requesters.append(requester)
        if not self.requesting:
            self.requesting = True
            await self.do_request(req)

    async def send_response(self, res: Base):
        self.agent.add_behaviour(MultiSenderBehaviour(res, self.requesters))
        self.requesters = []
        self.requesting = False

    async def do_request(self, req: Base):
        pass
