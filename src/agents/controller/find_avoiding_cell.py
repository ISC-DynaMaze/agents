from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from spade.behaviour import OneShotBehaviour

from agents.controller.maze.find_path import draw_path, find_path
from agents.controller.maze.grid import Maze
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class FindAvoidingCell(OneShotBehaviour):
    def __init__(self, maze: Maze):
        super().__init__()
        self.logger = logging.getLogger("FindAvoidingCell")
        self.maze = maze
    
