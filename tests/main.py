"""Main test on websocket server"""
import json
import subprocess
import time
import unittest
import urllib.error
import urllib.request

import websockets


class Server(unittest.IsolatedAsyncioTestCase):
    """Test that server responds to websocket request"""

    def setUp(self):
        port = time.time() % 100
        port = int(port) + 3000
        args = ["env/bin/python", "-m", "zoozl", str(port)]
        self.port = port
        # pylint: disable=consider-using-with
        self.proc = subprocess.Popen(args)
        time.sleep(2) # Let the process start
        self.assertIsNone(self.proc.poll(), "Process unexpectedly terminated")

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait()

    async def test(self):
        """call an open socket"""
        # pylint: disable=no-member
        async with websockets.connect(f"ws://localhost:{self.port}") as websocket:
            await websocket.ping()
            await websocket.send("Ābece")
            result = await websocket.recv()
            result = json.loads(result)
            self.assertEqual(result, {"author": "Oscar", "text": 'Hello!'})
        with self.assertRaises(urllib.error.HTTPError) as catch:
            with urllib.request.urlopen(f"http://localhost:{self.port}"):
                pass
        self.assertEqual(400, catch.exception.status)
        self.assertIn("Missing Sec-WebSocket-Key header", catch.exception.reason)
