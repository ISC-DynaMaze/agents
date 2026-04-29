from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.camera import CameraRequest, CameraResponse
from common.models.common import ReqResAdapter
from common.models.controller import DirectionResponse, PathRequest, PathResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class SendDirectionBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("SendDirectionBehaviour")

    async def on_start(self):
        self.maze = self.agent.maze
        self.path = self.agent.current_path
        self.photo_dir = Path("photos")

    async def run(self):
        # check for photo directory or create it
        self.photo_dir.mkdir(parents=True, exist_ok=True)
        # check for maze
        if self.maze is None:
            self.logger.error("Cannot send direction: maze is not initialized")
            return

        # request new image
        await self.req_image()
        img = await self.wait_for_new_image(timeout=10.0)
        if img is None:
            self.logger.error("Timed out waiting for camera image")
            return

        # detect aruco marker and update bot cell in maze
        corners, ids, _ = self.maze.detect_aruco_markers(img)
        if ids is None or len(ids) == 0:
            self.logger.error("No markers detected in camera image")
            return

        self.logger.info(f"Old bot cell: {self.maze.bot_cell}")
        # update bot cell in maze
        self.maze.set_bot_cell(corners, ids)
        self.logger.info(self.maze)
        self.logger.info(f"Updated bot cell: {self.maze.bot_cell}")

        # infer bot orientation based on marker corners
        orientation = self.get_bot_orientation(corners, ids, 13)
        if orientation is None:
            self.logger.error("Bot marker not found, cannot infer orientation")
        self.logger.info(f"Bot orientation: {orientation}")

        # request new path based on updated bot cell
        await self.req_path()
        path = await self.wait_for_path(timeout=10.0)
        if path is None:
            self.logger.error("Timed out waiting for path response")

        self.logger.info(f"New path: {path}")

        self.path = path
        next_cell = await self.get_next_cell()
        if next_cell is None:
            self.logger.info("Bot is already at destination")
            return

        # direction to the next cell in the path (from maze perspective)
        desired_direction = self.get_direction_from_path_step(path)
        if desired_direction is None:
            self.logger.error("Could not derive desired direction from path")
            return

        # get turn instruction to go from current bot orientation to desired direction
        turn = self.get_turn_instruction(
            current_heading=orientation, target_heading=desired_direction
        )
        if turn is None:
            self.logger.error("Could not compute turn instruction")
            return

        self.logger.info(
            f"Next path ready: {path} | next cell: {next_cell} | target heading: {desired_direction} | turn: {turn}"
        )

        await self.send_turn_message(turn)

    # send turn instruction to requester
    async def send_turn_message(self, turn: str):
        res = DirectionResponse(direction=turn)
        for requester in self.agent.direction_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))
        self.agent.direction_requesters = []
        self.agent.requesting_direction = False

    # request new image from camera agent
    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

    # request new path from controller receiver (which will trigger a new path computation with updated bot cell)
    async def req_path(self):
        req = PathRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.jid)))

    # wait for a new image file to appear in photo_dir that is not in known_files, then read and return it
    async def wait_for_new_image(self, timeout: float) -> np.ndarray:
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error("Timed out waiting for camera response message")
                    continue
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, CameraResponse)
                save_dir = Path("photos")
                img, _ = await res.decode_img(res.img, save_dir)
                return img
            except Exception as e:
                self.logger.error(
                    f"Error occurred while waiting for camera response: {e}"
                )
                continue

    # Wait for a new path response that is different from agent.current_path
    async def wait_for_path(self, timeout: float):
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error("Timed out waiting for path response message")
                    continue
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, PathResponse)
                return res.path
            except Exception as e:
                self.logger.error(f"Error occurred while waiting for path: {e}")
                continue

    # infer bot orientation based on position of bot marker corners
    def get_bot_orientation(self, corners, ids, bot_id):
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

            # FIXME: bot id 13 dx and dy > 0, for bot id 7, dx and dy < 0 
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
            self.logger.error("No path available to get next cell")
            return None
        return self.path[1]  # path[0] is current cell, path[1] is next cell
