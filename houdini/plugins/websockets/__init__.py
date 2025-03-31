
import os
from .streams import WebsocketReader, WebsocketWriter

from websockets import WebSocketClientProtocol
from websockets.server import serve
from houdini.plugins import IPlugin
from houdini.penguin import Penguin
from typing import Optional

import logging
import asyncio
import ssl

class HoudiniWebsockets(IPlugin):
    author = "Levi (Lekuru)"
    description = "Houdini websockets extension"
    version = "1.0.0"

    @property
    def config(self):
        return self.server.config

    @property
    def host(self) -> str:
        """The host of the websocket server."""
        return self.config.address

    @property
    def port(self) -> int:
        """The port of the websocket server."""
        return self.config.port + 1
    
    @property
    def certificate_path(self) -> Optional[str]:
        """The path to the certificate file (optional)"""
        return "/etc/letsencrypt/live/cphistory.pw/fullchain.pem"

    @property
    def key_path(self) -> Optional[str]:
        """The path to the key file (optional)"""
        return "/etc/letsencrypt/live/cphistory.pw/privkey.pem"

    @property
    def ssl_context(self) -> Optional[ssl.SSLContext]:
        """The SSL context for the websocket server."""
        if not self.certificate_path or not self.key_path:
            return None
        
        if not os.path.exists(self.certificate_path) or not os.path.exists(self.key_path):
            self.logger.warning("SSL certificate or key file does not exist. Running without SSL.")
            return None

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(self.certificate_path, self.key_path)
        return ssl_context

    def __init__(self, server) -> None:
        self.server = server
        self.logger = logging.getLogger(__name__)

    async def ready(self) -> None:
        server = serve(
            self.handler,
            self.host,
            self.port,
            ssl=self.ssl_context
        )

        async with server:
            self.logger.info(f'Websocket server listening on {self.host}:{self.port}')
            await asyncio.Future()

    async def handler(self, websocket: WebSocketClientProtocol, path: str) -> None:
        reader = WebsocketReader(websocket)
        writer = WebsocketWriter(websocket)
        penguin = Penguin(self.server, reader, writer)
        await penguin.run()
