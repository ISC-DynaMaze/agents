from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from spade.behaviour import PeriodicBehaviour

from common.models.robot import CameraStatus, StatusResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.robot.agent import RobotAgent


class StatusBehaviour(PeriodicBehaviour):
    agent: RobotAgent
    
    def __init__(self, recipient_jid: str, period: float, start_at: datetime | None = None):
        super().__init__(period, start_at)
        self.recipient_jid: str = recipient_jid

    async def run(self) -> None:
        status = StatusResponse(
            camera=CameraStatus(
                pan=self.agent.bot.getCameraPan(),
                tilt=self.agent.bot.getCameraTilt(),
            )
        )
        self.agent.add_behaviour(BaseSenderBehaviour(status, self.recipient_jid))
