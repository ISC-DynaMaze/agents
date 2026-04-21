import asyncio
import os

from agents.camera.agent import CameraAgent


async def main():
    sender_jid = os.environ.get("XMPP_JID", "camera@prosody")
    sender_password = os.environ.get("XMPP_PASSWORD", "top_secret")

    sender = CameraAgent(sender_jid, sender_password)

    await sender.start(auto_register=True)

    if not sender.is_alive():
        print("Camera agent couldn't connect. Check Prosody configuration.")
        await sender.stop()
        return

    print("Camera agent connected successfully. Running...")

    try:
        while sender.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down agent...")
    finally:
        await sender.stop()


if __name__ == "__main__":
    asyncio.run(main())
