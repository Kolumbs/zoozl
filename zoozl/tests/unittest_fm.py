"""Unittest framework test classes and functions."""

from unittest import TestCase
from unittest.mock import MagicMock

from zoozl import chatbot


class TestChatbot:
    """Object that supports testing directly with chatbot.

    >>> bot = TestChatbot()
    >>> bot.load()
    >>> bot.ask()
    >>> bot.close()
    """

    def __init__(self, conf=None):
        """Load object with callback and memory mocks."""
        self._callback = None
        self._memory = None
        self._interfaces = None
        self.bot = None

    def load(self, conf=None):
        """Load test chatbot with optional configuration."""
        self._callback = MagicMock()
        self._memory = MagicMock()
        self._interfaces = chatbot.InterfaceRoot(conf)
        self._interfaces.load()
        self.bot = chatbot.Chat("caller", self._callback, self._interfaces)

    def close(self):
        """Close interface."""
        self._interfaces.close()

    def last_call(self):
        """Return last received text message from callback."""
        return "\n".join(i.text for i in self.last_message().parts)

    def last_message(self):
        """Return last received message from callback."""
        try:
            self._callback.assert_called()
        except AssertionError:
            raise AssertionError("Bot did not make any responses.") from None
        return self._callback.call_args.args[0]

    def ask(self, *args, **kwargs):
        """Ask bot."""
        self.bot.ask(chatbot.Message(*args, **kwargs))

    def greet(self):
        """Receive greeting from bot."""
        self.bot.greet()

    def total_messages_sent(self):
        """Return number of messages sent back to callback so far."""
        return self._callback.call_count


class ChatbotUnittest(TestCase):
    """Unittest testcase that supports TestChatbot assert methods."""

    def setUp(self):
        """Initialise chatbot."""
        self.bot = TestChatbot()
        self.bot.load()

    def tearDown(self):
        """Close interface."""
        self.bot.close()

    def assert_response(self, *args, **kwargs):
        """Assert bot has responded."""
        expected = chatbot.Message(*args, **kwargs)
        received = self.bot.last_message()
        self.assertEqual(expected.author, received.author)
        self.assertEqual(expected.sent.year, received.sent.year)
        self.assertEqual(expected.sent.month, received.sent.month)
        self.assertEqual(expected.sent.day, received.sent.day)
        for i, val in enumerate(expected.parts):
            self.assertEqual(val, received.parts[i])
        return received

    def assert_response_with_any(self, *messages):
        """Assert bot has responded with any of provided messages."""
        not_found = 0
        received = self.bot.last_message()
        for m in messages:
            try:
                self.assert_response(m)
            except AssertionError:
                not_found += 1
        # We expect not_found messages to be exactly 1 less than expected
        if not_found + 1 != len(messages):
            self.fail(
                f"None of {messages} were found in response {received}",
            )
