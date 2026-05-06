import json
import logging
from pathlib import Path

from aiohttp import web
from spade.agent import Agent

from agents.logger.message_receiver import MessageReceiverBehaviour
from agents.logger.sender import SenderBehaviour


class LoggerAgent(Agent):
    PUBLIC_DIR = Path(__file__).parent / "public"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_clients: set[web.WebSocketResponse] = set()
        self.logger: logging.Logger = logging.getLogger("LoggerAgent")

    async def setup(self):
        self.web.app.middlewares.append(self.index_middleware)
        self.web.app.router.add_get("/api/status", self.handle_api_status)
        self.web.app.router.add_get("/ws", self.handle_websocket)
        self.web.app.router.add_static("/", self.PUBLIC_DIR, name="public")

        self.web.start(hostname="127.0.0.1", port=10000)

        receiver = MessageReceiverBehaviour()
        self.add_behaviour(receiver)

    @web.middleware
    async def index_middleware(self, request, handler):
        rel_path = Path(request.path).relative_to("/")
        full_path = self.PUBLIC_DIR / rel_path
        if full_path.exists() and full_path.is_dir():
            full_path /= "index.html"
            if full_path.exists():
                return web.FileResponse(full_path)
        return await handler(request)

    async def handle_api_status(self, request):
        data = {
            "status": "running",
            "jid": str(self.jid),
            "behaviours": len(self.behaviours),
        }
        return web.json_response(data)

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self.handle_ws_msg(msg.json())
                elif msg.type == web.WSMsgType.ERROR:
                    self.logger.warning(
                        f"WS connection closed with exception {ws.exception()}"
                    )
        finally:
            self.ws_clients.remove(ws)

        return ws

    async def handle_ws_msg(self, msg: dict):
        match msg["type"]:
            case "send":
                body: str = json.dumps(msg["msg"])
                self.add_behaviour(SenderBehaviour(body, msg["to"]))
            case "send-raw":
                self.add_behaviour(SenderBehaviour(msg["msg"], msg["to"]))

    async def send_ws(self, msg: dict):
        for ws in self.ws_clients:
            await ws.send_json(msg)
