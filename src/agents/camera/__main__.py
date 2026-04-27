import asyncio

from agents.camera.agent import CameraAgent
from common.launcher import Launcher


async def main():
    launcher: Launcher[CameraAgent] = Launcher(
        CameraAgent,
        {
            "jid": ("XMPP_JID", "camera@prosody"),
            "password": ("XMPP_PASSWORD", "top_secret"),
            "width": ("CAMERA_WIDTH", 768, int),
            "height": ("CAMERA_HEIGHT", 432, int),
        },
    )
    await launcher.launch()


if __name__ == "__main__":
    asyncio.run(main())
