import spade

from agents.logger.logger import LoggerAgent
from common.launcher import Launcher


async def main():
    launcher: Launcher[LoggerAgent] = Launcher(
        LoggerAgent,
        {
            "jid": ("XMPP_JID", "logger@isc-coordinator.lan"),
            "password": ("XMPP_PASSWORD", "top_secret"),
        },
        debug_loggers=["spade"],
    )
    await launcher.launch()


if __name__ == "__main__":
    spade.run(main())
