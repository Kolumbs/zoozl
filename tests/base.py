"""Abstract functions and classes for testing."""

import asyncio
import hmac
import json
import time
import unittest
import urllib.request

from zoozl import server, chatbot

from tests import load_configuration


class TestCase(unittest.IsolatedAsyncioTestCase):
    """Base class for all test cases."""


class ConfigurationMethods:
    """Methods to access configuration."""

    config_file = "tests/data/conf.toml"
    config = None

    def validate_configuration_key(self, key):
        """Check if configuration key is present."""
        # Load configuration if not already loaded
        if self.config is None:
            self.config = load_configuration(self.config_file)
        if key not in self.config:
            self.fail(f"Key '{key}' not present in configuration")

    @property
    def ws_port(self):
        """Return websocket port."""
        self.validate_configuration_key("websocket_port")
        return self.config["websocket_port"]

    @property
    def slack_port(self):
        """Return slack port."""
        self.validate_configuration_key("slack_port")
        return self.config["slack_port"]

    @property
    def slack_signing_secret(self):
        """Return slack secret."""
        self.validate_configuration_key("slack_signing_secret")
        return self.config["slack_signing_secret"]

    @property
    def slack_app_token(self):
        """Return slack token."""
        self.validate_configuration_key("slack_app_token")
        return self.config["slack_app_token"]

    @property
    def author(self):
        """Return author."""
        self.validate_configuration_key("author")
        return self.config["author"]


class SlackMethods:
    """Slack methods to communicate with zoozl slack server."""

    def get_slack_signature(self, body: bytes, timestamp: str):
        """Return slack signature."""
        stamp = b"v0:" + timestamp.encode("ascii") + b":" + body
        hasher = hmac.new(
            self.slack_signing_secret.encode("ascii"), stamp, digestmod="sha256"
        )
        return "v0=" + hasher.hexdigest()

    def send_slack_event(self, body: dict):
        """Send slack event."""
        body = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        timestamp = str(int(time.time()))
        headers["X-Slack-Request-Timestamp"] = timestamp
        headers["X-Slack-Signature"] = self.get_slack_signature(body, timestamp)
        request = urllib.request.Request(
            f"http://localhost:{self.slack_port}",
            headers=headers,
            data=body,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                if "Content-Length" in response.headers:
                    length = int(response.headers["Content-Length"])
                    body = response.read(length)
                else:
                    body = b""
                return response.status, response.headers, body
        except TimeoutError:
            self.fail(f"Request to {request.full_url} timed out")

    def send_challenge(self, challenge):
        """Send slack challenge."""
        body = {"type": "url_verification", "challenge": challenge}
        return self.send_slack_event(body)


class AbstractSlack(SlackMethods, ConfigurationMethods, TestCase):
    """Abstract testcases on slack server."""

    async def send_slack_event(self, body: dict):
        """Handle asynchronously server and sender slack event."""
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(asyncio.to_thread(super().send_slack_event, body))
        return task1.result()

    def assert_slack_called_with(self, mock, secret, channel, message):
        """Check if mock was called with arguments."""
        call = mock.call_args
        self.assertEqual(call.kwargs, {})
        self.assertEqual(len(call.args), 3, call.args)
        self.assertEqual(call.args[0], secret)
        self.assertEqual(call.args[1], channel)
        call_msg = call.args[2]
        self.assertEqual(call_msg.parts, message.parts)
        self.assertEqual(call_msg.author, message.author)

    async def asyncSetUp(self):
        """Set up slack server listening on socket."""
        self.conf = load_configuration(self.config_file)
        self.root = chatbot.InterfaceRoot(self.conf)
        self.root.load()
        self.server = await server.build_slack_server(
            self.root, self.conf["slack_port"], force_bind=True
        )
        self.assertTrue(self.server.is_serving())

    async def asyncTearDown(self):
        """Tear down slack server."""
        self.server.close()
        await self.server.wait_closed()
        self.root.close()


class AbstractServer(ConfigurationMethods, TestCase):
    """Object to support server testcases."""

    async def assert_answer(self, websocket, text, author="", timeout=3):
        """Check for answer."""
        try:
            async with asyncio.timeout(timeout):
                result = await websocket.recv()
        except TimeoutError:
            self.fail(f"Waited to receive {text} for longer than {timeout} seconds")
        result = json.loads(result)
        self.assertEqual(result, {"author": author, "text": text})
        return result
