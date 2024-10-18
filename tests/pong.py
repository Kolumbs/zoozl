"""Test zoozl ping plugin."""

import websockets

from tests._zoozl_server import AbstractServer, configure_server, terminate_server


def setUpModule():
    """Boot zoozl server in background."""
    configure_server("tests/data/ping.toml")


def tearDownModule():
    """Terminate zoozl server."""
    terminate_server()


class LongText(AbstractServer):
    """Handling long text messages."""

    async def test_long_text(self):
        """Send and receive long text."""
        text = "A" * 256
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await websocket.send(f'{{"text": "{text}"}}')
            await self.assert_answer(websocket, text)
