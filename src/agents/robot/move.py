from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from spade.behaviour import CyclicBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.forward_behaviour import ForwardBehaviour
from agents.robot.honk import HonkBehaviour
from agents.robot.leds_manager import State
from agents.robot.reposition import RepositionBehaviour
from agents.robot.turn import TurningBehaviour
from common.models.controller import (
    CubeOffset,
    CubesOffsetRequest,
    CubesOffsetResponse,
    DirectionRequest,
    DirectionResponse,
)
from common.models.robot import (
    Direction,
    LookAroundRequest,
    LookAroundResponse,
    SideType,
)
from common.sender import BaseSenderBehaviour
from common.utils import wait_for_response

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class MoveBehaviour(CyclicBehaviour):
    agent: RobotAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("MoveBehaviour")
        self.logger.setLevel(logging.DEBUG)
        self.turning_angle = 45
        self.speed = 20
        self.slow_speed = 10

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def pause_point(self):
        await self.agent.penalty.pause_point()

    async def on_start(self):
        self.surroundings = []  # mental state of what the robot saw
        self.bot.setBothPWM(self.speed)
        self.current_cube_offset = CubeOffset.NONE

    async def run(self):
        await self.pause_point()
        await self.reposition_to_nearest_cardinal()
        await self.pause_point()

        # ask for cubes offset for the next cell
        await self.ask_cubes_offset()
        cubes_offset = await self.wait_for_cubes_offset(timeout=5)
        if cubes_offset is None:
            self.logger.error("Timed out waiting for cubes offset response message")
            cubes_offset = CubeOffset.NONE

        # get direction to go
        # if we dont have info about current surrounding, ask controller
        # if lookaround gets anything other than exactly one open direction, ask controller
        if len(self.surroundings) < 1:
            self.logger.info(
                "No surroundings in mental state yet, asking for controller's input"
            )
            self.agent.leds.set_state(State.ASKING_CONTROLLER)
            await asyncio.sleep(0.5)  # to see the leds
            await self.ask_controller()
            direction = await self.wait_for_direction(timeout=3)
            self.agent.info(
                f"Moved {direction} (controller) --- surroundings not in mental state"
            )
        else:
            # get current surroundings and check which directions are open
            current_surrounding = await self.get_current_surrounding()
            await self.pause_point()
            if current_surrounding is None:
                self.logger.warning("Current surrounding is None")
                return

            free_directions = [
                direction
                for direction, side in current_surrounding
                if side == SideType.OPEN
            ]

            unkown_directions = [
                unkown
                for unkown, side in current_surrounding
                if side == SideType.UNKNOWN
            ]

            self.logger.debug(
                f"LOOKAROUND --- Free directions from lookaround: {free_directions}"
            )

            # if there is unkown direction we should not trust lookaround result and ask controller
            if len(free_directions) == 1 and len(unkown_directions) == 0:
                # get direction from lookaround
                direction = free_directions[0]
                self.logger.warning(f"Moved {direction} (lookaround)")
                self.agent.info(f"Moved {direction} (lookaround)")
            else:
                self.agent.leds.set_state(State.ASKING_CONTROLLER)
                await asyncio.sleep(0.5)  # to see the leds
                # get direction from controller
                await self.ask_controller()
                direction = await self.wait_for_direction(timeout=3)
                self.logger.warning(f"Moved {direction} (controller)")
                self.agent.info(f"Moved {direction} (controller)")

        # if there is no new path -- should be at target
        # FIXME: better way to detect target reached
        if direction is None:
            self.logger.error("Timed out waiting for direction response")
            self.agent.add_behaviour(HonkBehaviour())
            # self.agent.add_behaviour(DiscoBehaviour(period=0.5))
            self.kill()
            return

        # go to given direction
        await self.turn_and_go(direction, cubes_offset)
        await self.pause_point()
        self.logger.info(f"Moved {direction}")
        self.agent.leds.set_state(State.IDLE)

        self.bot.stop()
        self.current_cube_offset = cubes_offset
        self.logger.info(f"State of surroundings list after run: {self.surroundings}")
        await asyncio.sleep(5)
        # self.kill()  # stop the behaviour until next run when it will ask for surroundings again

    async def go_forward_to_cell_center_using_sensors(self, threshold: int = 500):
        cell_timing: float = 0.3
        if self.agent.calib.distance is not None:
            cell_timing = self.agent.calib.distance.half_cell
        else:
            self.logger.warning("Distance not calibrated, using fallback value")

        # slower speed so we can really stop at black line
        self.bot.setBothPWM(self.slow_speed)
        self.bot.forward()
        last_5_frames: list[int] = []
        check_interval: float = 0.02

        while True:
            # read sensor values and check if we are on a black line
            sensor_values: list[int] = self.bot.bottom_ir.readCalibrated()
            nb_studs: int = sum(1 for v in sensor_values if v > threshold)
            last_5_frames.append(nb_studs)
            last_5_frames = last_5_frames[-5:]
            is_on_stud: bool = sum(last_5_frames) > 0

            if is_on_stud:
                self.bot.stop()
                # scan for surroundings
                await asyncio.sleep(1)  # wait a bit to stabilize
                await self.pause_point()
                await self.ask_surroundings()
                # store next surrounding
                await self.store_next_surrounding()  # add directly to mental state

                self.logger.info("Pause at border")
                await asyncio.sleep(1)
                await self.pause_point()

                self.agent.leds.set_state(State.MOVING)

                # go forward to the middle of the cell
                self.bot.setBothPWM(self.speed)
                self.bot.forward()
                forward_behaviour = ForwardBehaviour()
                self.agent.add_behaviour(forward_behaviour)
                self.logger.info("Going to the center of the cell")
                # go forward for remaining calculated time
                await asyncio.sleep(cell_timing)
                forward_behaviour.kill()
                await forward_behaviour.join()
                self.bot.stop()
                return

            await asyncio.sleep(check_interval)

    async def turn_and_go(self, direction: str, cubes_offset: CubeOffset):
        self.agent.leds.set_state(State.MOVING)
        if direction == "left":
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(0.5)

        elif direction == "right":
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(0.5)

        elif direction == "back":
            for _ in range(4):
                await self.turn(direction=Direction.Right)
                await asyncio.sleep(1)

        await self.pause_point()

        # repositioning
        await self.reposition_to_nearest_cardinal()

        # calculate cube offset
        await self.ask_cubes_offset()
        cubes_offset = await self.wait_for_cubes_offset(timeout=5) # type: ignore
        if cubes_offset is None:
            self.logger.error("Timed out waiting for cubes offset response message")
            cubes_offset = CubeOffset.NONE

        # if there is a cube, position to avoid it
        # no need to reposition if we are already in the correct offset position
        if self.current_cube_offset == cubes_offset:
            self.logger.info(f"Already positioned to cube offset: {cubes_offset}")
            self.agent.info(f"Already positioned to cube offset: {cubes_offset}")
        # if we currently are in offset position but next cell has no cube, reposition to middle
        elif self.current_cube_offset != CubeOffset.NONE and cubes_offset == CubeOffset.NONE:
            if self.current_cube_offset == CubeOffset.LEFT:
                await self.position_to_cube_offset(CubeOffset.RIGHT)
            elif self.current_cube_offset == CubeOffset.RIGHT:
                await self.position_to_cube_offset(CubeOffset.LEFT)
        else :
            await self.position_to_cube_offset(cubes_offset)

        # go forward after turning or if direction is forward
        await self.go_forward_to_cell_center_using_sensors(
            threshold=self.agent.config.ir_threshold
        )

    async def turn(self, direction: Direction):
        angle = self.turning_angle
        # FIXME: workaround because calibration is not perfect
        if direction == Direction.Left:
            angle -= 5
        behaviour = TurningBehaviour(direction=direction, angle=angle)
        self.agent.add_behaviour(behaviour)
        await behaviour.join()

    async def position_to_cube_offset(self, offset: CubeOffset):
        await self.reposition_to_nearest_cardinal()
        self.agent.debug(f"In position_to_cube_offset with offset: {offset}")
        self.bot.setBothPWM(self.speed)

        if offset == CubeOffset.NONE:
            return
        
        if offset == CubeOffset.LEFT:
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(0.5)

            self.bot.forward()
            await asyncio.sleep(0.27)
            self.bot.stop()
            await asyncio.sleep(1)

            await self.turn(direction=Direction.Right)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(0.5)

        elif offset == CubeOffset.RIGHT:
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(0.5)

            self.bot.forward()
            await asyncio.sleep(0.27)
            self.bot.stop()
            await asyncio.sleep(1)

            await self.turn(direction=Direction.Left)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(0.5)
        
        self.agent.info(f"Positioned to cube offset: {offset}")
        self.current_cube_offset = offset
        
        await self.reposition_to_nearest_cardinal()

    async def reposition_to_nearest_cardinal(self):
        behaviour = RepositionBehaviour()
        self.agent.add_behaviour(behaviour)
        await behaviour.join()

    # ask controller where to go
    async def ask_controller(self):
        req = DirectionRequest()
        self.agent.add_behaviour(
            BaseSenderBehaviour(req, str(self.agent.controller_jid))
        )

    # wait for controller's response
    async def wait_for_direction(self, timeout: float) -> Optional[str]:
        res: Optional[DirectionResponse] = await wait_for_response(
            self, DirectionResponse, timeout
        )
        if res is None:
            self.logger.error("Timed out waiting for direction response message")
            return None
        return res.direction

    # ask for surroundings
    async def ask_surroundings(self):
        self.agent.leds.set_state(State.LOOKING_AROUND)
        req = LookAroundRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))

    async def wait_for_surroundings(
        self, timeout: float
    ) -> Optional[LookAroundResponse]:
        res: Optional[LookAroundResponse] = await wait_for_response(
            self, LookAroundResponse, timeout
        )
        if res is None:
            self.logger.error("Timed out waiting for surroundings response message")
        return res

    async def store_next_surrounding(self):
        self.bot.stop()  # should already be stopped but just in case
        result: Optional[LookAroundResponse] = await self.wait_for_surroundings(
            timeout=15
        )

        if result is None:
            self.logger.error("No response received for surroundings request")
            return

        self.agent.leds.show_surrounding(result)

        left, front, right = result.left, result.front, result.right
        self.logger.info(
            f"Received surroundings: left={left}, front={front}, right={right}"
        )
        self.surroundings.append(result)

    # returns surroundings of bot's current cell
    async def get_current_surrounding(self):
        if len(self.surroundings) < 1:
            self.logger.warning(
                "No current current surrounding in mental state"
            )  # should never happen when calling this function
            return None
        current = self.surroundings[-1]
        self.logger.debug(
            f"LOOKAROUND --- Current surroundings returned: left={current.left}, front={current.front}, right={current.right}"
        )

        self.agent.debug(
            f"Current surroundings: left={current.left}, front={current.front}, right={current.right}"
        )
        return [
            ("left", current.left),
            ("front", current.front),
            ("right", current.right),
        ]

    async def ask_cubes_offset(self):
        req = CubesOffsetRequest()
        self.agent.add_behaviour(
            BaseSenderBehaviour(req, str(self.agent.controller_jid))
        )

    async def wait_for_cubes_offset(
        self, timeout: float
    ) -> Optional[CubeOffset]:
        res: Optional[CubesOffsetResponse] = await wait_for_response(
            self, CubesOffsetResponse, timeout
        )
        if res is None:
            self.logger.error("Timed out waiting for cubes offset response message")
            return None
        return res.offset

