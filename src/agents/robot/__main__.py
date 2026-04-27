import asyncio

from agents.robot.agent import RobotAgent
from common.launcher import Launcher


async def main():
    launcher: Launcher[RobotAgent] = Launcher(
        RobotAgent,
        {
            "jid": ("XMPP_JID", "alberto-robot@isc-coordinator.lan"),
            "password": ("XMPP_PASSWORD", "top_secret"),
            "logger_jid": ("LOGGER_JID", "logger@isc-coordinator.lan"),
        },
        debug_loggers=["spade", "aioxmpp", "xmpp"],
    )
    await launcher.launch()


if __name__ == "__main__":
    asyncio.run(main())
