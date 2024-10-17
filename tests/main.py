"""Main test on websocket server."""

import asyncio
import json
import subprocess
import time
import unittest
import urllib.error
import urllib.request

import websockets


# pylint: disable=no-member,bad-classmethod-argument
class AbstractServer(unittest.IsolatedAsyncioTestCase):
    """Test that server responds to websocket request."""

    config_file = "tests/data/conf.toml"

    @classmethod
    def setUpClass(self):
        """Boot up server to listen on websocket."""
        port = time.time() % 100
        port = int(port) + 3000
        args = ["env/bin/python", "-m", "zoozl", str(port)]
        args.append("--conf")
        args.append(self.config_file)
        self.port = port
        # pylint: disable=consider-using-with
        self.proc = subprocess.Popen(args)
        time.sleep(2)  # Let the process start
        if self.proc.poll():
            raise RuntimeError("Process unexpectedly terminated")

    @classmethod
    def tearDownClass(self):
        """Safely tear down server."""
        self.proc.terminate()
        self.proc.wait()

    async def assert_answer(self, websocket, text, timeout=3):
        """Check for answer."""
        try:
            async with asyncio.timeout(timeout):
                result = await websocket.recv()
        except TimeoutError:
            self.fail(f"Waited to receive {text} for longer than {timeout} seconds")
        result = json.loads(result)
        self.assertEqual(result, {"author": "Zoozl", "text": text})
        return result


class SimpleServer(AbstractServer):
    """Simple test cases on server receiving and sending over websocket."""

    async def test(self):
        """Call an open socket."""
        greet = "Hello!"
        async with websockets.connect(f"ws://localhost:{self.port}") as websocket:
            await self.assert_answer(websocket, greet)
            await websocket.send("Ābece")
            pong = await websocket.ping()
            await pong
        with self.assertRaises(urllib.error.HTTPError) as catch:
            with urllib.request.urlopen(f"http://localhost:{self.port}"):
                pass
        self.assertEqual(400, catch.exception.status)
        self.assertIn("Missing Sec-WebSocket-Key header", catch.exception.reason)

    async def test_crash(self):
        """Close socket abruptly."""
        websocket = await websockets.connect(f"ws://localhost:{self.port}")
        await websocket.send("Ā")
        await websocket.recv()


class LongText(AbstractServer):
    """Handling long text messages."""

    config_file = "tests/data/ping.toml"

    async def test_long_text(self):
        """Send and receive long text."""
        text = "A" * 256
        async with websockets.connect(f"ws://localhost:{self.port}") as websocket:
            await websocket.send(f'{{"text": "{text}"}}')
            await self.assert_answer(websocket, text)


class ManyConnects(AbstractServer):
    """Connect to sockets multiple times."""

    async def test(self):
        """Try connecting multiple times."""
        async with websockets.connect(f"ws://localhost:{self.port}") as websocket:
            await websocket.send('{"text": "Ābece"}')
        async with websockets.connect(f"ws://localhost:{self.port}") as websocket:
            await websocket.send('{"text": "Ābece"}')
            await websocket.send('{"text": "Hello"}')
