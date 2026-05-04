from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Optional

from pydantic import BaseModel


class RotationMeasure(BaseModel):
    angle: float
    time: float


class RotationTest(BaseModel):
    target: float
    time: float
    obtained: float


class RotationCalibration(BaseModel):
    speed: float
    measures: list[RotationMeasure]
    tests: list[RotationTest]


class IRSensorCalibration(BaseModel):
    min: float
    max: float


class IRCalibration(BaseModel):
    sensors: list[IRSensorCalibration]


class DistanceCalibration(BaseModel):
    duration: float

    @property
    def half_cell(self) -> float:
        return self.duration / 2


class Calibration(BaseModel):
    PATH: ClassVar[Path] = Path("calibration.json")

    rotation: Optional[RotationCalibration]
    bottom_ir: Optional[IRCalibration]
    distance: Optional[DistanceCalibration]

    @staticmethod
    def load() -> Calibration:
        if not Calibration.PATH.exists():
            raise FileNotFoundError("Calibration not found")

        raw: str = Calibration.PATH.read_text()
        config: Calibration = Calibration.model_validate_json(raw)
        return config

    def save(self):
        raw: str = self.model_dump_json(indent=4)
        Calibration.PATH.write_text(raw)
