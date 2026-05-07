from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from spade.behaviour import OneShotBehaviour

from agents.controller.maze.find_path import a_star_search
from agents.controller.maze.grid import Maze
from agents.controller.send_direction import SendDirectionBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class FindAvoidingCellBehaviour(OneShotBehaviour):
    agent: ControllerAgent
    def __init__(self, maze: Maze):
        super().__init__()
        self.logger = logging.getLogger("FindAvoidingCell")
        self.maze = maze
    
    async def run(self) -> None:
        opp_start = (self.agent.opponent_current_cell.row, self.agent.opponent_current_cell.col)
        opp_target = (self.maze.opponent_target_cell.row, self.maze.opponent_target_cell.col)

        
        opponent_path = a_star_search(self.maze, opp_start, opp_target)

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
            self.logger.info(f"New temporary destination of robot avoidance : {safe_cell}")
            new_path = a_star_search(self.maze, (current.row, current.col), (safe_cell.row, safe_cell.col))
            if new_path :
                self.agent.current_path = new_path
                self.agent.add_behaviour(SendDirectionBehaviour())


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
                    # Récupérer le centre du marqueur (pixels)
                    c = corners[i][0]
                    center_x = int(c[:, 0].mean())
                    center_y = int(c[:, 1].mean())
                    row, col = self.maze.pixel_to_cell(center_x, center_y)
                    return self.maze.get_cell(row, col)
        return None
    
