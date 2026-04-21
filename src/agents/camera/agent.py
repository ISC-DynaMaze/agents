from spade.agent import Agent

from agents.camera.receiver import WaitForRequestBehaviour


class CameraAgent(Agent):
    async def setup(self):
        print(f"{self.jid} is ready.")
        self.add_behaviour(WaitForRequestBehaviour())
