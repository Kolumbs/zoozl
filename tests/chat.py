"""Testcases on chat interface"""
import unittest
from unittest.mock import MagicMock

from zoozl import chat


class AbstractTest(unittest.TestCase):
    """Abstract testcase on chat interface"""
    callback = MagicMock()

    def setUp(self):
        self.bot = chat.Chat("caller", self.callback)

    def tearDown(self):
        self.bot.close()

    def ask(self, *args, **kwargs):
        """ask to bot"""
        self.bot.ask(chat.Message(*args, **kwargs))

    def assert_response(self, *args, **kwargs):
        """assert bot has responded"""
        self.assertEqual(chat.Message(*args, **kwargs), self.callback.call_args.args[0])

    def get_text(self):
        """get received text"""
        return self.callback.call_args.args[0]


class Help(AbstractTest):
    """Testcase on chat help messaging"""

    def test_without_greet(self):
        """bot should respond with valid commands"""
        self.ask("kudos")
        self.assert_response("What would you like me to do?")
        self.ask("brrr")
        self.assert_response("I didn't get. Would you like me to send full list of commands?")
        self.ask("hello")
        self.assert_response("Try asking:\nplay games")

    def test_greet(self):
        """bot should help also when greeted"""
        self.bot.greet()
        self.ask("brr")
        self.assert_response("I didn't get. Would you like me to send full list of commands?")
        self.ask("hello")
        self.assert_response("Try asking:\nplay games")
        self.ask("play games")
        self.assert_response("what game you want to play? bulls and cows?")


class BullGame(AbstractTest):
    """Testcase on playing bull game"""

    def test(self):
        """play through a bull game"""
        self.ask("play games")
        self.ask("yes")
        self.assert_response("Guess 4 digit number")
        self.ask("1234")
