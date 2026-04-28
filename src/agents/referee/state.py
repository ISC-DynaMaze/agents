from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    TEAM_ASSIGN = auto()
    ROLE_ASSIGN = auto()