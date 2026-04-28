from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class GateTeam(StrEnum):
    TEAM1 = "LoopBreakers"
    TEAM2 = "CycleHunters"


class GateRole(StrEnum):
    START = "Start"
    END = "End"


@dataclass
class Gate:
    id: str
    team: Optional[GateTeam] = field(default=None)
    role: Optional[GateRole] = field(default=None)
