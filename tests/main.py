"""Main test on websocket server."""

import socket
import urllib.error
import urllib.request

import websockets

from tests._zoozl_server import AbstractServer, configure_server, terminate_server


def setUpModule():
    """Boot zoozl server in background."""
    configure_server()


def tearDownModule():
    """Terminate zoozl server."""
    terminate_server()


class SimpleServer(AbstractServer):
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


class ManyConnects(AbstractServer):
    """Connect to sockets multiple times."""

    async def test(self):
        """Try connecting multiple times."""
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await websocket.send('{"text": "Ābece"}')
        async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
            await websocket.send('{"text": "Ābece"}')
            await websocket.send('{"text": "Hello"}')


class WebsocketErrors(AbstractServer):
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
