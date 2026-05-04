from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel


class Config(BaseModel):
    PATH: ClassVar[Path] = Path("config.json")

    bot_aruco_id: int
    bot_aruco_rot: int = 0
    target_aruco_id: int
    arm_center_pos: tuple[int, int]
    maze_real_world_size_m: tuple[float, float]

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
