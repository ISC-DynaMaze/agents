from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Literal, Optional

from spade.behaviour import OneShotBehaviour

from common.models.controller import CubesOffsetResponse, CubesRequest, CubesResponse
from common.sender import BaseSenderBehaviour
from common.utils import wait_for_response

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


CubeOffset = Literal["none", "left", "right"]


class CubesOffsetBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("CubesOffsetBehaviour")

    async def run(self):
        await self.refresh_cubes()
        _ = await self.wait_for_cubes(timeout=10)
        offset = self.get_offset_for_next_cell()
        self.agent.info(f"Calculated cube offset: {offset}")
        await self.send_offset(offset)

    def get_offset_for_next_cell(self) -> CubeOffset:
        if self.agent.maze is None:
            self.logger.warning("No maze available for cube offset")
            return "none"

        if self.agent.current_path is None or len(self.agent.current_path) < 2:
            self.logger.warning("No next path cell available for cube offset")
            return "none"

        current_cell = self.agent.current_path[0]
        next_cell = self.agent.current_path[1]

        cube = self.get_cube_in_cell(next_cell)
        if cube is None:
            return "none"

        heading = self.get_maze_heading(current_cell, next_cell)
        if heading is None:
            return "none"

        quadrant = cube.get("quadrant")
        return self.quadrant_to_robot_offset(quadrant, heading)

    def get_cube_in_cell(self, cell: tuple[int, int]) -> dict | None:
        row, col = cell

        for cube in self.agent.maze.cubes:  # type: ignore
            if cube["row"] == row and cube["col"] == col:
                return cube

        return None

    # determine heading from current cell to next cell
    def get_maze_heading(
        self,
        current_cell: tuple[int, int],
        next_cell: tuple[int, int],
    ) -> str | None:
        row0, col0 = current_cell
        row1, col1 = next_cell

        d_row = row1 - row0
        d_col = col1 - col0

        if d_row == -1 and d_col == 0:
            return "up"
        if d_row == 1 and d_col == 0:
            return "down"
        if d_row == 0 and d_col == 1:
            return "right"
        if d_row == 0 and d_col == -1:
            return "left"

        return None

    # relative to robot heading
    def quadrant_to_robot_offset(
        self,
        quadrant: str | None,
        heading: str,
    ) -> CubeOffset:
        if quadrant is None:
            return "none"

        match heading:
            case "up":
                # example: bot going up, cube in top left or bottom left -> robot should head on its right
                if quadrant in ("top_left", "bottom_left"):
                    return "right"
                if quadrant in ("top_right", "bottom_right"):
                    return "left"

            case "down":
                if quadrant in ("top_left", "bottom_left"):
                    return "left"
                if quadrant in ("top_right", "bottom_right"):
                    return "right"

            case "right":
                if quadrant in ("top_left", "top_right"):
                    return "right"
                if quadrant in ("bottom_left", "bottom_right"):
                    return "left"

            case "left":
                if quadrant in ("top_left", "top_right"):
                    return "left"
                if quadrant in ("bottom_left", "bottom_right"):
                    return "right"

        return "none"

    async def refresh_cubes(self):
        req = CubesRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))

    async def wait_for_cubes(self, timeout: float) -> Optional[str]:
        res: Optional[CubesResponse] = await wait_for_response(
            self, CubesResponse, timeout
        )
        if res is None:
            self.logger.error("Timed out waiting for cubes response message")
            return None
        return res  # type: ignore

    async def send_offset(self, offset: CubeOffset):
        res = CubesOffsetResponse(offset=offset)

        for requester in self.agent.cubes_offset_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))

        self.agent.cubes_offset_requesters = []
        self.agent.requesting_cubes_offset = False
