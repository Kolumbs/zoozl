"""Testcases on chat interface."""

import unittest
from unittest.mock import MagicMock

from zoozl import chatbot


class AbstractTest(unittest.TestCase):
    """Abstract testcase on chat interface."""

    callback = MagicMock()
    memory = MagicMock()

    def setUp(self):
        """Initialise chatbot."""
        self.interfaces = chatbot.InterfaceRoot()
        self.interfaces.load()
        self.bot = chatbot.Chat("caller", self.callback, self.interfaces)

    def tearDown(self):
        """Close interface."""
        self.interfaces.close()

    def ask(self, *args, **kwargs):
        """Ask to bot."""
        self.bot.ask(chatbot.Message(*args, **kwargs))

    def assert_response(self, *args, **kwargs):
        """Assert bot has responded."""
        self.callback.assert_called()
        expected = chatbot.Message(*args, **kwargs)
        received = self.callback.call_args.args[0]
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
        received = self.callback.call_args.args[0]
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

    def assert_help_response(self):
        """Assert last message is of help type response."""
        self.assert_response_with_any(
            "You can try to play games.",
            "I can't do much. I can only play a game.",
            "I can play games.",
        )

    def assert_hello_response(self):
        """Assert last message if of hello type response."""
        self.assert_response_with_any(
            "Hello", "Hey", "Hello, hello. What do you want to do?"
        )

    def get_text(self):
        """Get received text."""
        return self.callback.call_args.args[0]


class Help(AbstractTest):
    """Testcase on chat help messaging."""

    def test_without_greet(self):
        """Bot should respond with valid commands."""
        self.ask("kudos")
        self.assert_help_response()
        self.ask("brrr")
        self.assert_help_response()
        self.ask("hello")
        self.assert_hello_response()

    def test_greet(self):
        """Bot should help also when greeted."""
        self.bot.greet()
        self.ask("brr")
        self.assert_help_response()
        self.ask("hello")
        self.assert_hello_response()
        self.ask("play games")
        self.assert_response("what game you want to play? bulls and cows?")


class BullGame(AbstractTest):
    """Testcase on playing bull game."""

    def test(self):
        """Play through a bull game."""
        self.ask("play game")
        self.assert_response("what game you want to play? bulls and cows?")
        self.ask("yes")
        self.assert_response("Guess 4 digit number")
        self.ask("1234")
        self.ask("cancel")
