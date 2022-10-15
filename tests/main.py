"""Main test on websocket server"""
import json
import subprocess
import time
import unittest
import urllib.error
import urllib.request

import websockets


# pylint: disable=no-member,bad-classmethod-argument
class Server(unittest.IsolatedAsyncioTestCase):
    """Test that server responds to websocket request"""

    @classmethod
    def setUpClass(self):
        port = time.time() % 100
        port = int(port) + 3000
        args = ["env/bin/python", "-m", "zoozl", str(port)]
        self.port = port
        # pylint: disable=consider-using-with
        self.proc = subprocess.Popen(args)
        time.sleep(2) # Let the process start
        if self.proc.poll():
            raise RuntimeError("Process unexpectedly terminated")

    @classmethod
    def tearDownClass(self):
        self.proc.terminate()
        self.proc.wait()

    async def assert_answer(self, websocket, text):
        """checks for answer"""
        result = await websocket.recv()
        result = json.loads(result)
        self.assertEqual(result, {"author": "Oscar", "text": text})
        return result

    async def test(self):
        """call an open socket"""
        greet = 'Hello! What would you like me to do?'
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
        """close socket abruptly"""
        websocket = await websockets.connect(f"ws://localhost:{self.port}")
        await websocket.send("Ā")
        await websocket.recv()
