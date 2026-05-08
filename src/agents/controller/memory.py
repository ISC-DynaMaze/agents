from common.models.controller import Orientation


class Memory:
    ORIENTATION_ORDER: list[Orientation] = ["right", "down", "left", "right"]

    def __init__(self):
        self.last_pos: tuple[int, int] = (0, 0)
        self.last_orientation: Orientation = "right"

    def set(self, pos: tuple[int, int], orientation: Orientation):
        self.last_pos = pos
        self.last_orientation = orientation

    def get(self) -> tuple[tuple[int, int], Orientation]:
        return self.last_pos, self.last_orientation

    def apply_delta(self, displacement: tuple[int, int], rotation: int):
        i1: int = self.ORIENTATION_ORDER.index(self.last_orientation)
        i2: int = (i1 + rotation) % 4
        self.last_orientation = self.ORIENTATION_ORDER[i2]
        x, y = self.last_pos
        dx, dy = displacement
        dx, dy = self._rotate_displacement(dx, dy, i1)
        self.last_pos = (x + dx, y + dy)

    def _rotate_displacement(self, dx: int, dy: int, rot: int) -> tuple[int, int]:
        match rot:
            case 1:
                return -dy, dx
            case 2:
                return -dx, -dy
            case 3:
                return dy, -dx
            case _:
                return dx, dy
