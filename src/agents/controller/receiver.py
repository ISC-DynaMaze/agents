from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from agents.controller.bot_detection import BotDetectionBehaviour
from agents.controller.detect_cubes import DetectCubesBehaviour
from agents.controller.find_path import FindPathBehaviour
from agents.controller.get_obstacles import ObstaclesBehaviour
from agents.controller.maze.grid import Maze
from agents.controller.obstacles_position import ObstacleRelativePositionBehaviour
from agents.controller.photo import RequestPhotoBehaviour
from agents.controller.remove_obstacles import RemoveObstaclesBehaviour
from agents.controller.send_direction import SendDirectionBehaviour
from common.models.camera import CameraResponse
from common.models.common import Request, Response
from common.models.controller import (
    AngleRequest,
    CubesRequest,
    DirectionRequest,
    DirectionResponse,
    MazeRequest,
    ObstaclePositionRequest,
    ObstacleRemoveRequest,
    ObstaclesRequest,
    ObstaclesResponse,
    PathRequest,
    PathResponse,
)
from common.receiver import BaseReceiverBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class ReceiverBehaviour(BaseReceiverBehaviour):
    agent: ControllerAgent

    def __init__(
        self,
        save_dir: Path,
        path_dir: Path,
        obstacles_dir: Path,
        cubes_dir: Path,
    ):
        super().__init__()
        self.logger = logging.getLogger("ReceiverBehaviour")
        self.save_dir: Path = save_dir
        self.path_dir: Path = path_dir
        self.obstacles_dir: Path = obstacles_dir
        self.cubes_dir: Path = cubes_dir

    async def on_start(self) -> None:
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.path_dir.mkdir(parents=True, exist_ok=True)
        self.obstacles_dir.mkdir(parents=True, exist_ok=True)
        self.cubes_dir.mkdir(parents=True, exist_ok=True)
        return await super().on_start()

    def error(self, msg: str):
        self.logger.error(msg)
        self.agent.error(msg)

    async def request_photo(self):
        ask_photo = RequestPhotoBehaviour(self.agent.camera_jid)
        self.agent.add_behaviour(ask_photo)

    async def request_direction(self):
        maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
        if maze is None:
            self.error("Cannot compute direction, maze is not available")
            return
        ask_direction = SendDirectionBehaviour(maze)
        self.agent.add_behaviour(ask_direction)

    async def request_obstacles(self):
        maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
        if maze is None:
            self.error("Cannot find obstacles, maze is not available")
            return
        get_obstacles = ObstaclesBehaviour(maze)
        self.agent.add_behaviour(get_obstacles)

    async def request_obstacles_pos(self):
        maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
        if maze is None:
            self.error("Cannot compute obstacle positions, maze is not available")
            return
        get_obstacles_pos = ObstacleRelativePositionBehaviour(maze)
        self.agent.add_behaviour(get_obstacles_pos)

    async def request_obstacles_rem(self):
        rem_obstacle = RemoveObstaclesBehaviour()
        self.agent.add_behaviour(rem_obstacle)

    async def request_cubes(self):
        maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
        if maze is None:
            self.error("Cannot detect cubes, maze is not available")
            return
        self.agent.requesting_cubes = True
        detect_cubes = DetectCubesBehaviour(maze)
        self.agent.add_behaviour(detect_cubes)

    async def on_request(self, sender_jid: str, req: Request):
        match req:
            case MazeRequest():
                await self.agent.maze_manager.on_request(sender_jid, req)

            case AngleRequest():
                self.agent.angle_requesters.append(sender_jid)
                if not self.agent.requesting_image:
                    await self.request_photo()

            case PathRequest():
                self.agent.path_requesters.append(sender_jid)
                maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
                if maze is None:
                    self.logger.error("Received path request but maze is not available")
                    self.agent.error("Received path request but maze is not available")
                    return
                find_path = FindPathBehaviour(maze=maze, output_dir=self.path_dir)
                self.agent.add_behaviour(find_path)

            case DirectionRequest():
                self.agent.direction_requesters.append(sender_jid)
                if not self.agent.requesting_direction:
                    await self.request_direction()

            case ObstaclesRequest():
                self.agent.obstacles_requesters.append(sender_jid)
                if not self.agent.requesting_obstacles:
                    await self.request_obstacles()

            case ObstaclePositionRequest():
                await self.request_obstacles_pos()

            case ObstacleRemoveRequest():
                await self.request_obstacles_rem()

            case CubesRequest():
                self.agent.cubes_requesters.append(sender_jid)
                if not self.agent.requesting_cubes:
                    await self.request_cubes()

    async def on_response(self, sender_jid: str, res: Response):
        match res:
            case CameraResponse():
                await self.agent.camera.on_receive(res)
                self.agent.requesting_image = False

                img, filepath = await res.decode_img(self.save_dir)

                if len(self.agent.angle_requesters) != 0:
                    bot_detection = BotDetectionBehaviour(img)
                    self.agent.add_behaviour(bot_detection)

                if len(self.agent.path_requesters) != 0:
                    maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
                    if maze is None:
                        self.error(
                            "Received path request but maze is not available"
                        )
                        return
                    find_path = FindPathBehaviour(maze=maze, output_dir=self.path_dir)
                    self.agent.add_behaviour(find_path)

                if len(self.agent.obstacles_requesters) != 0:
                    maze: Optional[Maze] = await self.agent.maze_manager.get_or_fetch()
                    if maze is None:
                        self.error("Received obstacle request but maze is not available")
                        return
                    get_obstacles = ObstaclesBehaviour(maze)
                    self.agent.add_behaviour(get_obstacles)

            case PathResponse(path=path):
                self.logger.info(f"Path: {path}")
                self.agent.current_path = path

            case DirectionResponse(direction=direction):
                self.logger.info(f"Received direction response: {direction}")

            case ObstaclesResponse(obstacles=obstacles):
                self.logger.info(f"Obstacles: {obstacles}")
                self.agent.maze.obstacles = obstacles  # type: ignore

    async def on_raw(self, sender_jid: str, msg: str):
        if "camera" in sender_jid:
            res = CameraResponse(img=msg)
            return await self.on_response(sender_jid, res)
        return await super().on_raw(sender_jid, msg)
