import asyncio
import logging

import spade

from agents.logger.logger import LoggerAgent

logging.basicConfig(level=logging.DEBUG)

# Enable SPADE and XMPP specific logging
for log_name in ["spade", "aioxmpp", "xmpp"]:
    log = logging.getLogger(log_name)
    log.setLevel(logging.DEBUG)
    log.propagate = True


async def main():
    agent = LoggerAgent("logger@isc-coordinator.lan", "plsnohack")
    await agent.start()
    print("Agent started")

    try:
        while agent.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await agent.stop()


if __name__ == "__main__":
    spade.run(main())
