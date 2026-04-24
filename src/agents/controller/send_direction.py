from __future__ import annotations

import asyncio
import math
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from spade.behaviour import OneShotBehaviour

from common.models.camera import CameraRequest
from common.models.controller import DirectionResponse, PathRequest
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class SendDirectionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()

    async def on_start(self):
        self.maze = self.agent.maze
        self.path = self.agent.current_path
        self.photo_dir = Path("photos")
        return super().on_start()

    async def run(self):
        # check for maze
        if self.maze is None:
            self.agent.logger.error("Cannot send direction: maze is not initialized")
            return

        # request new image
        await self.req_image()
        img = await self.wait_for_new_image(timeout=10.0)
        if img is None:
            self.agent.logger.error("Timed out waiting for camera image")
            return

        # detect aruco marker and update bot cell in maze
        corners, ids, _ = self.maze.detect_aruco_markers(img)
        if ids is None or len(ids) == 0:
            self.agent.logger.error("No markers detected in camera image")
            return

        self.agent.logger.info(f"Old bot cell: {self.maze.bot_cell}")
        # update bot cell in maze
        self.maze.set_bot_cell(corners, ids)
        self.agent.logger.info(self.maze)
        self.agent.logger.info(f"Updated bot cell: {self.maze.bot_cell}")

        # infer bot orientation based on marker corners
        orientation = self.get_bot_orientation(corners, ids, 13)
        if orientation is None:
            self.agent.logger.error("Bot marker not found, cannot infer orientation")
        self.agent.logger.info(f"Bot orientation: {orientation}")

        # request new path based on updated bot cell
        previous_path = self.agent.current_path
        await self.req_path()
        path = await self.wait_for_path(previous_path, timeout=10.0)
        if path is None:
            self.agent.logger.error("Timed out waiting for path response")

        self.agent.logger.info(f"New path: {path}")

        self.path = path
        next_cell = await self.get_next_cell()
        if next_cell is None:
            self.agent.logger.info("Bot is already at destination")
            return

        # direction to the next cell in the path (from maze perspective)
        desired_direction = self.get_direction_from_path_step(path)
        if desired_direction is None:
            self.agent.logger.error("Could not derive desired direction from path")
            return

        # get turn instruction to go from current bot orientation to desired direction
        turn = self.get_turn_instruction(
            current_heading=orientation, target_heading=desired_direction
        )
        if turn is None:
            self.agent.logger.error("Could not compute turn instruction")
            return

        self.agent.logger.info(
            f"Next path ready: {path} | next cell: {next_cell} | target heading: {desired_direction} | turn: {turn}"
        )

        await self.send_turn_message(turn)

    # send turn instruction to requester
    async def send_turn_message(self, turn: str):
        res = DirectionResponse(path=turn)
        for requester in self.agent.direction_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))

    # request new image from camera agent
    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

    # request new path from controller receiver (which will trigger a new path computation with updated bot cell)
    async def req_path(self):
        req = PathRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))

    # wait for a new image file to appear in photo_dir that is not in known_files, then read and return it
    async def wait_for_new_image(self, timeout: float):
        deadline = time.monotonic() + timeout
        known_files = {f.name for f in self.photo_dir.glob("photo_*.jpg")}

        while time.monotonic() < deadline:
            candidates = sorted(
                self.photo_dir.glob("photo_*.jpg"),
                key=lambda p: p.stat().st_mtime,
            )
            for file_path in reversed(candidates):
                if file_path.name in known_files:
                    continue

                img = cv2.imread(str(file_path))
                if img is not None:
                    return img

            await asyncio.sleep(0.2)

        return None

    # Wait for a new path response that is different from agent.current_path
    async def wait_for_path(self, previous_path, timeout: float):

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current_path = self.agent.current_path
            if current_path is not None and current_path != previous_path:
                return current_path
            await asyncio.sleep(0.2)
        return None

    # infer bot orientation based on position of bot marker corners
    def get_bot_orientation(self, corners, ids, bot_id: int = 7):
        if ids is None:
            return None

        ids_flat = ids.flatten()
        for i, marker_id in enumerate(ids_flat):
            if int(marker_id) != bot_id:
                continue

            marker = corners[i][0]
            tl, tr, br, bl = marker

            # compute vector from marker center to top middle point, use that to determine orientation
            center = marker.mean(axis=0)
            top_mid = (tl + tr) / 2.0
            vec = top_mid - center
            dx = float(vec[0])
            dy = float(vec[1])

            if math.fabs(dx) >= math.fabs(dy):
                return "right" if dx > 0 else "left"
            return "down" if dy > 0 else "up"

        return None

    # get direction from first step in path to next cell
    def get_direction_from_path_step(self, path):
        if path is None or len(path) < 2:
            return None

        row0, col0 = path[0]
        row1, col1 = path[1]
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

    # compute the turn instruction needed to go from current bot orientation to next path direction
    def get_turn_instruction(self, current_heading: str, target_heading: str):
        order = ["up", "right", "down", "left"]
        if current_heading not in order or target_heading not in order:
            return None

        current_idx = order.index(current_heading)
        target_idx = order.index(target_heading)
        delta = (target_idx - current_idx) % 4

        if delta == 0:
            return "front"
        if delta == 1:
            return "right"
        if delta == 2:
            return "back"
        return "left"

    # get next cell in path
    async def get_next_cell(self):
        if self.path is None or len(self.path) < 2:
            self.agent.logger.error("No path available to get next cell")
            return None
        return self.path[1]  # path[0] is current cell, path[1] is next cell
