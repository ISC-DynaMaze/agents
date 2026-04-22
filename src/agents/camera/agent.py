from spade.agent import Agent

from agents.camera.receiver import WaitForRequestBehaviour


class CameraAgent(Agent):
    async def setup(self):
        print(f"{self.jid} is ready.")
        self.add_behaviour(WaitForRequestBehaviour())

    def __init__(self, jid: str, password: str, width: int, height: int):
        super().__init__(jid, password)
        self.width: int = width
        self.height: int = height
