import spade

from agents.referee.agent import RefereeAgent
from common.launcher import Launcher


async def main():
    launcher: Launcher[RefereeAgent] = Launcher(
        RefereeAgent,
        {
            "jid": ("XMPP_JID", "referee@isc-coordinator.lan"),
            "password": ("XMPP_PASSWORD", "top_secret"),
            "mqtt_host": ("MQTT_HOST", "isc-coordinator.lan"),
            "mqtt_port": ("MQTT_PORT", 1883, int),
        },
        debug_loggers=["spade"],
    )
    await launcher.launch()


if __name__ == "__main__":
    spade.run(main())
