"""Testcases on chat interface."""

from zoozl.tests import ChatbotUnittest


class AbstractTest(ChatbotUnittest):
    """Abstract testcase on chat interface."""

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


class Help(AbstractTest):
    """Testcase on chat help messaging."""

    def test_without_greet(self):
        """Bot should respond with valid commands."""
        self.bot.ask("kudos")
        self.assert_help_response()
        self.bot.ask("brrr")
        self.assert_help_response()
        self.bot.ask("hello")
        self.assert_hello_response()

    def test_greet(self):
        """Bot should help also when greeted."""
        self.bot.greet()
        self.bot.ask("brr")
        self.assert_help_response()
        self.bot.ask("hello")
        self.assert_hello_response()
        self.bot.ask("play games")
        self.assert_response("what game you want to play? bulls and cows?")


class BullGame(AbstractTest):
    """Testcase on playing bull game."""

    def test(self):
        """Play through a bull game."""
        self.bot.ask("play game")
        self.assert_response("what game you want to play? bulls and cows?")
        self.bot.ask("yes")
        self.assert_response("Guess 4 digit number")
        self.bot.ask("1234")
        self.bot.ask("cancel")
