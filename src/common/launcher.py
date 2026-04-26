import asyncio
import logging
import os
import signal
from typing import Any, Callable, Generic, Optional, Type, TypeVar, Union

from spade.agent import Agent

T = TypeVar("T", bound=Agent)
ParamValue = Union[
    tuple[str, Any], tuple[str, Any, Callable[[Any], Any]], Callable[[], Any]
]


class Launcher(Generic[T]):
    def __init__(
        self,
        agent_cls: Type[T],
        env_vars: Optional[dict[str, ParamValue]] = None,
        debug_loggers: Optional[list[str]] = None,
    ) -> None:
        self.logger = logging.getLogger("Launcher")
        self.agent_cls: Type[T] = agent_cls
        self.env_vars: dict[str, ParamValue] = env_vars or {}
        self.debug_loggers: list[str] = debug_loggers or []

    def config_loggers(self):
        logging.basicConfig(level=logging.DEBUG)

        for log_name in self.debug_loggers:
            log = logging.getLogger(log_name)
            log.setLevel(logging.DEBUG)
            log.propagate = True

    def make_agent(self) -> T:
        vars = {}
        for param_name, param_value in self.env_vars.items():
            value = None
            if isinstance(param_value, tuple):
                env_name = param_value[0]
                default = param_value[1]
                value = os.environ.get(env_name, default)
                if len(param_value) > 2:
                    func = param_value[2]
                    value = func(value)
            elif callable(param_value):
                value = param_value()
            else:
                raise ValueError(
                    f"invalid parameter value for {param_name}: {param_value}"
                )
            vars[param_name] = value

        agent: T = self.agent_cls(**vars, verify_security=False)
        return agent

    def wire_signals(self, agent: T):
        loop = asyncio.get_running_loop()

        def stop():
            self.logger.info("Received stop signal")
            asyncio.create_task(agent.stop())

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop)

    async def mainloop(self, agent: T):
        try:
            while agent.is_alive():
                self.logger.debug("Agent is alive and running...")
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            await agent.stop()
            self.logger.info("Agent stopped by user")
        except asyncio.CancelledError:
            pass

    async def launch(self):
        self.config_loggers()

        agent: T
        try:
            agent = self.make_agent()
            self.logger.info("Agent created, attempting to start...")
            await agent.start(auto_register=True)
        except Exception as e:
            self.logger.error(f"Error starting agent: {str(e)}", exc_info=True)
            return

        self.logger.info("Agent started successfully!")
        self.wire_signals(agent)
        await self.mainloop(agent)
