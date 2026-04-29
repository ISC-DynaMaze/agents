from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from spade.behaviour import CyclicBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.disco import DiscoBehaviour
from agents.robot.forward_behaviour import ForwardBehaviour
from agents.robot.honk import HonkBehaviour
from agents.robot.reposition import RepositionBehaviour
from agents.robot.turn import TurningBehaviour
from common.models.common import ReqResAdapter
from common.models.controller import DirectionRequest, DirectionResponse
from common.models.robot import Direction
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class MoveBehaviour(CyclicBehaviour):
    agent: RobotAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("MoveBehaviour")
        self.logger.setLevel(logging.DEBUG)
        self.turning_angle = 45

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def on_start(self):
        self.surroundings = []  # mental state of what the robot saw
        self.bot.setBothPWM(20)

    async def run(self):
        # reposition bot
        await self.reposition_to_nearest_cardinal()
        # await self.go_forward_for(0.15)
        # self.logger.info("Moved forward for 0.15 seconds")

        # get next surrounding
        # await self.get_next_surrounding()  # add directly to mental state

        # check if we have already seen the surroundings for current cell
        if len(self.surroundings) == 1:
            self.logger.info("No surroundings in mental state")
            return

        # get current surroundings and check which directions are open
        # current_surrounding = await self.get_current_surrounding()

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
        direction = await self.wait_for_direction(timeout=5.0)
        if direction is None:
            self.logger.error("Timed out waiting for direction response")
            self.agent.add_behaviour(HonkBehaviour())
            self.agent.add_behaviour(DiscoBehaviour(period=0.5))
            self.kill()
            return

        self.logger.info(f"Controller directed to go: {direction}")
        await self.turn_and_go(direction)
        self.logger.info(f"Moved {direction}")

        self.bot.stop()
        await asyncio.sleep(1)
        # self.kill()  # stop the behaviour until next run when it will ask for surroundings again

    # depending on the free directions, move forward or turn and move forward
    async def go_forward_for(self, seconds: float):
        self.bot.forward()
        forward_behaviour = ForwardBehaviour()
        self.agent.add_behaviour(forward_behaviour)
        await asyncio.sleep(seconds)
        forward_behaviour.kill()
        await forward_behaviour.join()
        self.bot.stop()

    async def turn_and_go(self, direction: str):
        if direction == "left":
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Left)
            self.logger.info("TURNED LEEEEEEFT")
            await asyncio.sleep(0.3)

        elif direction == "right":
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Right)
            self.logger.info("TURNED RIGHHHHHHHHT")
            await asyncio.sleep(0.3)

        # go forward after turning or if direction is forward
        await self.go_forward_for(0.7)

    async def turn(self, direction: Direction):
        angle = self.turning_angle
        # FIXME: workaround because calibration is not perfect
        if direction == Direction.Left:
            angle -= 5
        behaviour = TurningBehaviour(direction=direction, angle=angle)
        self.agent.add_behaviour(behaviour)
        await behaviour.join()

    async def reposition_to_nearest_cardinal(self):
        behaviour = RepositionBehaviour()
        self.agent.add_behaviour(behaviour)
        await behaviour.join()

    # ask controllor where to go
    async def ask_controller(self):
        req = DirectionRequest()
        self.agent.add_behaviour(
            BaseSenderBehaviour(req, str(self.agent.controller_jid))
        )

    # wait for controller's response
    async def wait_for_direction(self, timeout: float) -> Optional[str]:
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error(
                        "Timed out waiting for direction response message"
                    )
                    return None
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
