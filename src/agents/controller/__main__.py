import asyncio

from agents.controller.agent import ControllerAgent
from common.launcher import Launcher


async def main():
    launcher: Launcher[ControllerAgent] = Launcher(
        ControllerAgent,
        {
            "jid": ("XMPP_JID", "alberto-ctrl@isc-coordinator.lan"),
            "password": ("XMPP_PASSWORD", "top_secret"),
            "camera_jid": ("CAMERA_JID", "camera@isc-coordinator.lan"),
            "logger_jid": ("LOGGER_JID", "logger@isc-coordinator.lan"),
        },
        debug_loggers=["spade", "aioxmpp", "xmpp"],
    )
    await launcher.launch()


if __name__ == "__main__":
    asyncio.run(main())
