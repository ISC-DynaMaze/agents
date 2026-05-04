from pydantic import BaseModel


class Config(BaseModel):
    bot_aruco_id: int
    bot_aruco_rot: int = 0
    target_aruco_id: int
    arm_center_pos: tuple[int, int]
    maze_real_world_size_m: tuple[float, float]
