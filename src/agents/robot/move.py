import asyncio
import logging
from typing import Any

from spade.behaviour import CyclicBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from common.models.common import ReqResAdapter
from common.models.controller import DirectionRequest, DirectionResponse
from common.sender import BaseSenderBehaviour


class MoveBehaviour(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        print("########## MoveBehaviour initialized")
        self.logger = logging.getLogger("MoveBehaviour")
        self.logger.setLevel(logging.DEBUG)
    
    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def on_start(self):
        print("########## MoveBehaviour started")
        self.surroundings = []  # mental state of what the robot saw

    async def run(self):
        print("########## MoveBehaviour run")
        #await self.go_forward_for(0.15)
        self.logger.info("Moved forward for 0.15 seconds")

        # get next surrounding
       # await self.get_next_surrounding()  # add directly to mental state

        # check if we have already seen the surroundings for current cell
        if len(self.surroundings) == 1:
            self.logger.info("No surroundings in mental state")
            return

        # get current surroundings and check which directions are open
        #current_surrounding = await self.get_current_surrounding()

        # check free direction in current surroundings
        # free_directions = [
        #     direction for direction, status in current_surrounding if status == "open"
        # ]

        # TODO: implement logic when check for surroundings implemented
        # if len(free_directions) == 1:
        #     self.agent.logger.info(f"Only one free direction: {free_directions[0]}")
        #     await self.turn_and_go(free_directions[0])
        #     self.agent.logger.info(f"Moved {free_directions[0]}")

        # if len(free_directions) > 1:
            # self.agent.logger.info(f"Multiple free directions: {free_directions}")

        # ask controller where to go
        await self.ask_controller()
        direction = await self.wait_for_direction(timeout=10.0)
        if direction is None:
            self.logger.error("Timed out waiting for direction response")
            return
        self.logger.info(f"Controller directed to go: {direction}")
        await self.turn_and_go(direction)
        self.logger.info(f"Moved {direction}")

        self.bot.stop()
        self.kill()  # stop the behaviour until next run when it will ask for surroundings again

    # depending on the free directions, move forward or turn and move forward
    async def go_forward_for(self, seconds: float):
        self.bot.forward()
        await asyncio.sleep(seconds)
        self.bot.stop()

    async def turn_and_go(self, direction: str):
        if direction == "left":
            self.logger.info("TURNED LEEEEEEFT")
            self.bot.left()
            await asyncio.sleep(0.3)
            self.bot.stop()
        elif direction == "right":
            self.logger.info("TURNED RIGHHHHHHHHT")
            self.bot.right()
            await asyncio.sleep(0.3)
            self.bot.stop()

        # go forward after turning or if direction is forward
        await self.go_forward_for(0.1)

    # ask controllor where to go
    async def ask_controller(self):
        req = DirectionRequest()
        self.agent.add_behaviour(
            BaseSenderBehaviour(req, str(self.agent.controller_jid))
        )

    # wait for controller's response
    async def wait_for_direction(self, timeout: float):
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error("Timed out waiting for direction response message")
                    continue
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, DirectionResponse)
                return res.direction
            except Exception as e:
                self.logger.error(f"Error occurred while waiting for direction: {e}")
                continue

    # ask for surroundings
    # TODO: adapt with actual response
    async def ask_surroundings(self):
        # req = SurroundingsRequest()
        # self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))
        directions = {"left": "wall", "front": "open", "right": "wall"}
        return directions

    async def get_next_surrounding(self):
        self.bot.stop()  # stop the bot before asking for surroundings
        next_surrounding = await self.ask_surroundings()
        if next_surrounding is None:
            self.logger.error("No response received for surroundings request")
            return
        else:
            self.surroundings.append(next_surrounding)

    # returns list of tuples with direction and status of current surrounding
    async def get_current_surrounding(self):
        if len(self.surroundings) == 1:
            self.logger.warning(
                "No current current surrounding in mental state"
            )  # should never happen when calling this function
            return None
        return list(self.surroundings[-2].items())