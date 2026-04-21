from spade.behaviour import Message, OneShotBehaviour

from models.base import Base


class SenderBehaviour(OneShotBehaviour):
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
