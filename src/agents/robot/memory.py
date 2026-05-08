from common.models.common import RelativeDirection


class Memory:
    DIRECTIONS: list[RelativeDirection] = [
        RelativeDirection.FRONT,
        RelativeDirection.RIGHT,
        RelativeDirection.BACK,
        RelativeDirection.LEFT,
    ]
    DIR_OFFSETS: list[tuple[int, int]] = [
        (1, 0),
        (0, 1),
        (-1, 0),
        (0, -1),
    ]

    def __init__(self):
        self.pos_offset: tuple[int, int] = (0, 0)
        self.rot_offset: int = 0

    def move(self, direction: RelativeDirection):
        delta: int = self.DIRECTIONS.index(direction)
        self.rot_offset = (self.rot_offset + delta) % 4
        x1, y1 = self.pos_offset
        dx, dy = self.DIR_OFFSETS[self.rot_offset]
        self.pos_offset = (x1 + dx, y1 + dy)

    def reset(self):
        self.pos_offset = (0, 0)
        self.rot_offset = 0
