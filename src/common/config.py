from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict


class Config(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    PATH: ClassVar[Path] = Path("config.json")

    bot_aruco_id: int
    """ArUco marker id of the robot"""

    bot_aruco_rot: Literal[0, 90, 180, 270] = 0
    """ArUco marker rotation on the robot. 0° is up facing forward"""

    target_aruco_id: int
    """ArUco marker id of the target"""

    arm_center_pos: tuple[int, int]
    """Position of the center of the robot arm base on the camera image, in pixels"""

    maze_real_world_size_m: tuple[float, float]
    """Width and height of the maze IRL, in meters"""

    ir_threshold: int = 500
    """Threshold for IR detection with the bottom sensors"""

    @staticmethod
    def load() -> Config:
        if not Config.PATH.exists():
            raise FileNotFoundError("Configuration not found")

        raw: str = Config.PATH.read_text()
        config: Config = Config.model_validate_json(raw)
        return config

    def save(self):
        raw: str = self.model_dump_json(indent=4)
        Config.PATH.write_text(raw)
