from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from spade.behaviour import CyclicBehaviour

from agents.robot.AlphaBot2 import AlphaBot2
from agents.robot.forward_behaviour import ForwardBehaviour
from agents.robot.honk import HonkBehaviour
from agents.robot.leds_manager import State
from agents.robot.reposition import RepositionBehaviour
from agents.robot.turn import TurningBehaviour
from common.models.common import ReqResAdapter
from common.models.controller import DirectionRequest, DirectionResponse
from common.models.robot import (
    Direction,
    LookAroundRequest,
    LookAroundResponse,
    SideType,
)
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
        self.speed = 20
        self.slow_speed = 10

    @property
    def bot(self) -> AlphaBot2:
        return self.agent.bot

    async def on_start(self):
        self.surroundings = []  # mental state of what the robot saw
        self.bot.setBothPWM(self.speed)

    async def run(self):
        # reposition bot
        await self.reposition_to_nearest_cardinal()

        # get direction to go
        # if we dont have info about current surrounding, ask controller
        # if lookaround gets anything other than exactly one open direction, ask controller
        if len(self.surroundings) < 2:
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
        await self.turn_and_go(direction)
        self.logger.info(f"Moved {direction}")
        self.agent.leds.set_state(State.IDLE)

        self.bot.stop()
        self.logger.info(f"State of surroundings list after run: {self.surroundings}")
        await asyncio.sleep(5)
        # self.kill()  # stop the behaviour until next run when it will ask for surroundings again

    async def go_forward_to_cell_center_using_sensors(self, threshold: int = 500):
        # read time it took to go across one cell from calib file
        calib_path = Path("calibration_data") / "distance_calibration_data.json"
        cell_timing = None
        try:
            if calib_path.exists():
                with open(calib_path, "r") as f:
                    data = json.load(f)
                    cell_timing = float(data.get("distance_time"))
        except Exception as e:
            self.logger.warning(f"Could not read calibration file: {e}")

        # slower speed so we can really stop at black line
        self.bot.setBothPWM(self.slow_speed)
        self.bot.forward()
        last_5_frames = []
        check_interval = 0.02

        while True:
            # read sensor values and check if we are on a black line
            sensor_values = self.bot.bottom_ir.readCalibrated()
            nb_studs = sum(1 for v in sensor_values if v > threshold)
            last_5_frames.append(nb_studs)
            last_5_frames = last_5_frames[-5:]
            is_on_stud = sum(last_5_frames) > 0

            if is_on_stud:
                self.bot.stop()
                # scan for surroundings
                await asyncio.sleep(1)  # wait a bit to stabilize
                await self.ask_surroundings()
                # store next surrounding
                await self.store_next_surrounding()  # add directly to mental state

                self.logger.info("Pause at border")
                await asyncio.sleep(1)

                self.agent.leds.set_state(State.MOVING)

                # go forward to the middle of the cell
                self.bot.setBothPWM(self.speed)
                self.bot.forward()
                forward_behaviour = ForwardBehaviour()
                self.agent.add_behaviour(forward_behaviour)
                self.logger.info("Going to the center of the cell")
                # go forward for remaining calculated time
                await asyncio.sleep(cell_timing / 2 if cell_timing else 0.3)
                forward_behaviour.kill()
                await forward_behaviour.join()
                self.bot.stop()
                return

            await asyncio.sleep(check_interval)

    async def turn_and_go(self, direction: str):
        self.agent.leds.set_state(State.MOVING)
        if direction == "left":
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Left)
            await asyncio.sleep(0.3)

        elif direction == "right":
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(1)
            await self.turn(direction=Direction.Right)
            await asyncio.sleep(0.3)

        # go forward after turning or if direction is forward
        await self.go_forward_to_cell_center_using_sensors()

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
    async def ask_surroundings(self):
        self.agent.leds.set_state(State.LOOKING_AROUND)
        req = LookAroundRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))

    async def wait_for_surroundings(self, timeout: float):
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error(
                        "Timed out waiting for surroundings response message"
                    )
                    return None
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, LookAroundResponse)
                return res
            except Exception as e:
                self.logger.error(f"Error occurred while waiting for surroundings: {e}")
                continue

    async def store_next_surrounding(self):
        self.bot.stop()  # should already be stopped but just in case
        result = await self.wait_for_surroundings(timeout=15)

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
        if len(self.surroundings) < 2:
            self.logger.warning(
                "No current current surrounding in mental state"
            )  # should never happen when calling this function
            return None
        current = self.surroundings[-2]
        self.logger.debug(
            f"LOOKAROUND --- Current surroundings returned: left={current.left}, front={current.front}, right={current.right}"
        )  # -2 because we already stored the surroundings of the next cell in mental state when we entered it

        self.agent.debug(
            f"Current surroundings: left={current.left}, front={current.front}, right={current.right}"
        )
        return [
            ("left", current.left),
            ("front", current.front),
            ("right", current.right),
        ]
