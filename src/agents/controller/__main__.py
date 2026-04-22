import asyncio
import logging
import os

from agents.controller.agent import ControllerAgent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("AlphaBotAgent")

# Enable SPADE and XMPP specific logging
for log_name in ["spade", "aioxmpp", "xmpp"]:
    log = logging.getLogger(log_name)
    log.setLevel(logging.DEBUG)
    log.propagate = True


async def main():
    xmpp_jid = os.environ.get("XMPP_JID", "alberto-ctrl@isc-coordinator.lan")
    xmpp_password = os.environ.get("XMPP_PASSWORD", "top_secret")

    logger.info("Starting AlphaBot XMPP Agent")
    logger.info(f"XMPP JID: {xmpp_jid}")
    logger.info(f"XMPP Password: {'*' * len(xmpp_password)}")

    try:
        agent = ControllerAgent(
            jid=xmpp_jid, password=xmpp_password, verify_security=False
        )

        logger.info("Agent created, attempting to start...")
        await agent.start(auto_register=True)
        logger.info("Agent started successfully!")

        try:
            while agent.is_alive():
                logger.debug("Agent is alive and running...")
                await asyncio.sleep(10)  # Log every 10 seconds that agent is alive
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            await agent.stop()
            logger.info("Agent stopped by user.")
    except Exception as e:
        logger.error(f"Error starting agent: {str(e)}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except Exception as e:
        logger.critical(f"Critical error in main loop: {str(e)}", exc_info=True)
