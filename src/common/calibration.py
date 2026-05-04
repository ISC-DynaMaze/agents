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


class Calibration(BaseModel):
    rotation: RotationCalibration
    bottom_ir: IRCalibration
    distance: DistanceCalibration
