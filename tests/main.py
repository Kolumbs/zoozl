"""Main test on websocket server."""

import socket
import urllib.error
import urllib.request

import websockets

from tests import base as bs
from tests.fixtures.zoozl_server import configure, terminate


def setUpModule():
    """Boot zoozl server in background."""
    configure()


def tearDownModule():
    """Terminate zoozl server."""
    terminate()


class SimpleServer(bs.AbstractServer):
    """Simple test cases on server receiving and sending over websocket."""

    async def test(self):
        """Call an open socket."""
        greet = "Hello!"
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await self.assert_answer(websocket, greet)
            await websocket.send("Ābece")
            pong = await websocket.ping()
            await pong
        with self.assertRaises(urllib.error.HTTPError) as catch:
            with urllib.request.urlopen(f"http://localhost:{self.ws_port}"):
                pass
        self.assertEqual(400, catch.exception.status)
        self.assertIn("Bad Request", catch.exception.reason)

    async def test_crash(self):
        """Close socket abruptly."""
        websocket = await websockets.connect(f"ws://localhost:{self.ws_port}")
        await websocket.send("Ā")
        await websocket.recv()


class ManyConnects(bs.AbstractServer):
    """Connect to sockets multiple times."""

    async def test(self):
        """Try connecting multiple times."""
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await websocket.send('{"text": "Ābece"}')
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await websocket.send('{"text": "Ābece"}')
            await websocket.send('{"text": "Hello"}')


class WebsocketErrors(bs.AbstractServer):
    """Negative test cases for connecting to websocket server."""

    def test_buffers(self):
        """Send too large buffer."""
        self.assert_error("A" * 2**20, 501)
        self.assert_error("GET", 408)
        self.assert_error("GET " + "A" * 2**20, 414)
        self.assert_error("GET / HTTP/1.1", 408)
        self.assert_error("GET / HTTP/1.1\r\n\r\n\r\n", 400)

    def test_timeout(self):
        """Lock server into timeout while kill connection."""
        try:
            self.assert_error("GET", 408, timeout=1)
        except TimeoutError:
            pass
        self.assert_error("GET", 408)

    def assert_error(self, message: str, status: int, timeout=5):
        """Check for error."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(("localhost", self.ws_port))
        sock.send(message.encode("ascii"))
        try:
            self.assertIn(str(status), sock.recv(4056).decode("ascii"))
        finally:
            sock.close()


class SlackServer(bs.SlackMethods, bs.AbstractServer):
    """Testcase for slack services."""

    def test_challenge(self):
        """Test slack challenge request."""
        my_challenge = "Ābece"
        _, headers, body = self.send_challenge(my_challenge)
        self.assertIn("Content-Type", headers)
        self.assertIn("text/plain", headers["Content-Type"])
        self.assertIn("Content-Length", headers)
        self.assertEqual(len(body), int(headers["Content-Length"]))
        self.assertEqual(body.decode("utf-8"), my_challenge)
