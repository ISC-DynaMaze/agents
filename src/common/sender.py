from typing import Sequence

from spade.behaviour import Message, OneShotBehaviour

from common.models.base import Base


class BaseSenderBehaviour(OneShotBehaviour):
    def __init__(self, data: Base, to_jid: str):
        super().__init__()
        self.data: Base = data
        self.to_jid: str = to_jid

    def make_message(self) -> Message:
        return Message(
            to=self.to_jid,
            body=self.data.model_dump_json(),
            metadata={"performative": "inform"},
        )

    async def run(self) -> None:
        msg: Message = self.make_message()
        await self.send(msg)


class MultiSenderBehaviour(OneShotBehaviour):
    def __init__(self, data: Base, to_jids: Sequence[str]):
        super().__init__()
        self.data: Base = data
        self.to_jids: Sequence[str] = to_jids

    def make_message(self, to_jid: str) -> Message:
        return Message(
            to=to_jid,
            body=self.data.model_dump_json(),
            metadata={"performative": "inform"},
        )

    async def run(self) -> None:
        for jid in self.to_jids:
            msg: Message = self.make_message(jid)
            await self.send(msg)
