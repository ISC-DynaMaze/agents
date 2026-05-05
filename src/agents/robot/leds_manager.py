from enum import Enum, auto

from rpi_ws281x import Adafruit_NeoPixel

from agents.robot.AlphaBot2 import AlphaBot2
from common.models.robot import LookAroundResponse, SideType


class State(Enum):
    IDLE = auto()
    LOOKING_AROUND = auto()
    MOVING = auto()
    ASKING_CONTROLLER = auto()


class LedsManager:
    SURROUNDINGS_COLOR: dict[SideType, tuple[int, int, int]] = {
        SideType.UNKNOWN: (255, 255, 0),
        SideType.WALL: (255, 0, 0),
        SideType.OPEN: (0, 255, 0),
    }
    STATE_COLORS: dict[State, tuple[int, int, int]] = {
        State.IDLE: (0, 0, 0),
        State.LOOKING_AROUND: (100, 100, 200),
        State.MOVING: (255, 0, 255),
        State.ASKING_CONTROLLER: (255, 200, 100),
    }

    def __init__(self, bot: AlphaBot2):
        self.bot: AlphaBot2 = bot

    @property
    def leds(self) -> Adafruit_NeoPixel:
        return self.bot.back_leds

    def on(self):
        self.leds.setBrightness(255)

    def off(self):
        self.leds.setBrightness(0)

    def set(self, i: int, color: tuple[int, int, int]):
        self.leds.setPixelColorRGB(i, *color)

    def set_all(self, color: tuple[int, int, int]):
        if color == (0, 0, 0):
            self.off()
        else:
            self.on()
            for i in range(4):
                self.set(i, color)

    def show(self):
        self.leds.show()

    def show_surrounding(self, surroundings: LookAroundResponse):
        left: SideType = surroundings.left
        front: SideType = surroundings.front
        right: SideType = surroundings.right

        left_col: tuple[int, int, int] = self.SURROUNDINGS_COLOR[left]
        front_col: tuple[int, int, int] = self.SURROUNDINGS_COLOR[front]
        right_col: tuple[int, int, int] = self.SURROUNDINGS_COLOR[right]

        self.on()
        self.set(0, right_col)
        self.set(1, front_col)
        self.set(2, front_col)
        self.set(3, left_col)
        self.show()

    def set_state(self, state: State):
        color: tuple[int, int, int] = self.STATE_COLORS[state]
        self.set_all(color)
        self.show()
