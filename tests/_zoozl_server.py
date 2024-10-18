"""Zoozl server configuration."""

import asyncio
import json
import socket
import subprocess
import time
import tomllib
import unittest


# Store server process
ZOOZL_SERVER_PROCESS = None
# Store configuration
CONFIGURATION = None


def socket_check(port, timeout=2):
    """Check if socket is open on port for a given timeout in seconds.

    Otherwise raise an exception.
    """
    time_left = timeout
    while time_left > 0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("localhost", port))
            return
        except ConnectionRefusedError:
            time.sleep(0.1)
            time_left -= 0.1
        finally:
            sock.close()
    raise AssertionError(f"Socket on port {port} did not open up within {timeout} secs")


def terminate_server(error: str = ""):
    """Terminate zoozl server."""
    global ZOOZL_SERVER_PROCESS
    if ZOOZL_SERVER_PROCESS is None:
        raise RuntimeError("Server process not started, run `configure_server` first")
    ZOOZL_SERVER_PROCESS.terminate()
    try:
        ZOOZL_SERVER_PROCESS.wait(timeout=1)
    except subprocess.TimeoutExpired:
        ZOOZL_SERVER_PROCESS.kill()
        ZOOZL_SERVER_PROCESS.wait()
    stdout = ZOOZL_SERVER_PROCESS.stdout.read().decode("utf-8")
    ZOOZL_SERVER_PROCESS.stdout.close()
    ZOOZL_SERVER_PROCESS = None
    if error:
        msg = str(error) + "\n" + stdout
        raise AssertionError(msg) from None
    else:
        print(stdout)


def configure_server(config_file: str = "tests/data/conf.toml"):
    """Set up server configuration and start server process."""
    global ZOOZL_SERVER_PROCESS, CONFIGURATION
    with open(config_file, "rb") as file:
        CONFIGURATION = tomllib.load(file)
    args = ["env/bin/python", "-m", "zoozl", "--force-bind"]
    args.append("--conf")
    args.append(config_file)
    ZOOZL_SERVER_PROCESS = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    try:
        if CONFIGURATION["websocket_port"]:
            socket_check(CONFIGURATION["websocket_port"])
    except Exception as e:
        terminate_server(e)


class AbstractServer(unittest.IsolatedAsyncioTestCase):
    """Test that server responds to websocket request."""

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

    @property
    def ws_port(self):
        """Return websocket port."""
        if CONFIGURATION is None:
            raise RuntimeError("Please run `setUpModule` before accessing `ws_port`")
        return CONFIGURATION["websocket_port"]
