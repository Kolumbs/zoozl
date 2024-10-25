"""Test zoozl ping plugin."""

import websockets

from tests import base as bs
from tests.fixtures.zoozl_server import configure, terminate


def setUpModule():
    """Boot zoozl server in background."""
    configure("tests/data/ping.toml")


def tearDownModule():
    """Terminate zoozl server."""
    terminate()


class LongText(bs.AbstractServer):
    """Handling long text messages."""

    config_file = "tests/data/ping.toml"

    async def test_long_text(self):
        """Send and receive long text."""
        text = "A" * 256
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await websocket.send(f'{{"text": "{text}"}}')
            await self.assert_answer(websocket, text)
