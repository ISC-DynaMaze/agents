from typing import TYPE_CHECKING

from spade.behaviour import CyclicBehaviour

from agents.camera.photo import CapturePhotoBehaviour

if TYPE_CHECKING:
    from agents.camera.agent import CameraAgent


class WaitForRequestBehaviour(CyclicBehaviour):
    agent: CameraAgent

    async def run(self):
        print("Waiting for request...")
        msg = await self.receive(timeout=9999)
        if msg:
            print("Received camera image request.")
            requester_jid = str(msg.sender)
            capture_behaviour = CapturePhotoBehaviour(requester_jid)
            self.agent.add_behaviour(capture_behaviour)
