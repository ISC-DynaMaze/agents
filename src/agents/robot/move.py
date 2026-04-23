import asyncio
from typing import Any

from spade.behaviour import CyclicBehaviour

from agents.robot.agent import RobotAgent
from common.models.controller import (
    MoveRequest,
    PathRequest,
    SurroundingsRequest,
    SurroundingsResponse,
)
from common.sender import BaseSenderBehaviour


class MoveBehaviour(CyclicBehaviour):
    agent: RobotAgent

    def __init__(self):
        super().__init__()
        self.bot = None

    def on_start(self):
        self.bot = self.agent.bot
        self.bot.setBothPWM(40)

    async def run(self):
        await self._go_forward_for(0.15)

        # surroundings is a list of tuples (direction, is_free) (str, bool)
        surroundings = await self.ask_surroundings()
        if surroundings is None:
            self.agent.logger.error("No response received for surroundings request")
            return

        # left - front - right
        free_directions = [direction for direction, is_free in surroundings if is_free]

        if len(free_directions) == 1:
            self.agent.logger.info(f"Only one free direction: {free_directions[0]}")
            await self.turn_and_go(free_directions[0])
            self.agent.logger.info(f"Moved {free_directions[0]}")
            return

        if len(free_directions) > 1:
            self.agent.logger.info(f"Multiple free directions: {free_directions}")
            # ask controller where to go
            direction = await self.ask_controller()
            self.agent.logger.info(f"Controller directed to go: {direction}")
            await self.turn_and_go(direction)
            self.agent.logger.info(f"Moved {direction}")
            return

        self.bot.stop()
        self.kill()  # stop the behaviour until next run when it will ask for surroundings again

    # depending on the free directions, move forward or turn and move forward
    async def go_forward_for(self, seconds: float):
        self.bot.forward()
        await asyncio.sleep(seconds)
        self.bot.stop()

    async def turn_and_go(self, direction: str):
        if direction == "left":
            self.bot.left()
            await asyncio.sleep(0.2)
            self.bot.stop()
        elif direction == "right":
            self.bot.right()
            await asyncio.sleep(0.2)
            self.bot.stop()

        # go forward after turning or if direction is forward
        await self.go_forward_for(0.2)

    # ask for surroundings
    # TODO: adapt with actual response
    async def ask_surroundings(self):
        # req = SurroundingsRequest()
        # self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))
        directions = [("left", True), ("front", False), ("right", False)]
        return directions

    # ask controllor where to go
    # TODO: adapt with actual response
    async def ask_controller(self):
        # req = MoveRequest()
        # self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.controller_jid)))
        direction = "front"
        return direction