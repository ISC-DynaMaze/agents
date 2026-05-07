from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional
import numpy as np

import cv2
from spade.behaviour import OneShotBehaviour

from agents.controller.maze.find_path import a_star_search
from agents.controller.maze.grid import Maze
from agents.controller.send_direction import SendDirectionBehaviour
from common.models.camera import CameraRequest, CameraResponse
from common.sender import BaseSenderBehaviour
from common.utils import wait_for_response

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class FindAvoidingCellBehaviour(OneShotBehaviour):

    agent: ControllerAgent

    def __init__(self, maze: Maze):
        super().__init__()
        self.logger = logging.getLogger("FindAvoidingCell")
        self.maze = maze
    
    async def run(self) -> None:

        await self.req_image()
        img: Optional[np.ndarray] = await self.wait_for_new_image(timeout=10.0)
        if img is None:
            self.logger.error("Timed out waiting for camera image")
            return

        self.opponent_current_cell = self.get_opponent_current_cell(img)

        opp_start = (self.opponent_current_cell.row, self.opponent_current_cell.col)
        opp_target = (self.maze.opponent_target_cell.row, self.maze.opponent_target_cell.col)
        self.logger.info(f"[Opponent] Robot position : {opp_start}, Robot target : {opp_target}")

        self.agent.opponent_path= a_star_search(self.maze, opp_start, opp_target)
        self.logger.info(f"[Opponent] Path : {self.agent.opponent_path}")

        current = self.maze.bot_cell
        safe_cell = None

        for move in range(4):
            if self.maze.is_valid_move(current.row, current.col, move):
                nr = current.row + (move == 0) - (move == 1)
                nc = current.col + (move == 2) - (move == 3)
                
                if (nr, nc) not in opponent_path: # type: ignore
                    safe_cell = self.maze.grid[nr][nc]
                    break 

        if safe_cell:
            self.logger.info(f"New temporary destination of bot avoidance : {safe_cell}")
            new_path = a_star_search(self.maze, (current.row, current.col), (safe_cell.row, safe_cell.col))
            if new_path :
                self.agent.current_path = new_path
                self.agent.add_behaviour(SendDirectionBehaviour())
                self.logger.info(f"[New Path] {self.agent.current_path}")


    def get_opponent_current_cell(self, image):
        corners, ids, _ = self.maze.detect_aruco_markers(image)
        
        if ids is not None:
            known_ids = [
                self.agent.config.bot_aruco_id,          
                self.agent.config.target_aruco_id,       
                self.agent.config.opponent_target_aruco_id 
            ]
            
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id not in known_ids:
                    c = corners[i][0]
                    center_x = int(c[:, 0].mean())
                    center_y = int(c[:, 1].mean())
                    row, col = self.maze.pixel_to_cell(center_x, center_y)
                    return self.maze.get_cell(row, col)
        return None

    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

    async def wait_for_new_image(self, timeout: float) -> Optional[np.ndarray]:
        res: Optional[CameraResponse] = await wait_for_response(
            self, CameraResponse, timeout
        )
        if res is None:
            self.logger.error("Timed out waiting for camera response message")
            return None
        save_dir = Path("photos")
        img, _ = await res.decode_img(save_dir)
        return img
    
