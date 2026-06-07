"""Example single-agent plugin to showcase zoozl chatbot mechanics."""

import random

from zoozl.chatbot import Agent as BaseAgent, Message


def count_bulls_cows(challenge, number):
    """Count bulls and cows."""
    bulls = 0
    cows = 0
    for i, guess in enumerate(challenge):
        for j, value in enumerate(number):
            if guess == value:
                if i == j:
                    bulls += 1
                else:
                    cows += 1
                break
    return bulls, cows


class Agent(BaseAgent):
    """Default bundled agent."""

    helps = (
        "I can't do much. I can only play a game.",
        "I can play games.",
        "You can try to play games.",
    )
    greets = ("Hello", "Hey", "Hello, hello. What do you want to do?")

    async def greet(self, package):
        """Greet the user once."""
        if package.conversation.ongoing:
            package.callback("Hey. What would you like me to do?")
        else:
            package.callback("Hello!")
            package.callback(
                "I can do few things. Ask me for example to play games or something."
            )
            package.conversation.ongoing = True

    async def consume(self, package):
        """Handle one user message."""
        text = package.last_message_text.strip().lower()
        if text == "cancel":
            package.conversation.data.pop("game", None)
            package.conversation.data.pop("bull_number", None)
            package.callback(random.choice(self.helps))
            return
        if "game" in package.conversation.data:
            self.bull_game(package)
            return
        if "hello" in text or text in {"hi", "hey", "how are you"}:
            package.callback(random.choice(self.greets))
            return
        if "play game" in text or "play games" in text:
            package.callback(Message("what game you want to play? bulls and cows?"))
            return
        if text in {"bull", "bulls and cows", "bulls & cows", "yes"}:
            package.conversation.data["game"] = "bull_game"
            package.callback("OK. Let's play bulls and cows")
            self.bull_game(package)
            return
        package.callback(random.choice(self.helps))

    def bull_game(self, package):
        """Play a number guessing game."""
        if "bull_number" in package.conversation.data:
            number = package.last_message_text
            if len(number) != 4:
                package.callback(Message("Give number with exactly 4 digits"))
            elif len(set(number)) != len(number):
                package.callback("Digits must be unique in number")
            else:
                bulls, cows = count_bulls_cows(
                    number, package.conversation.data["bull_number"]
                )
                if bulls == 4:
                    package.callback("Congrats. You guessed right")
                    package.conversation.data.pop("game", None)
                    package.conversation.data.pop("bull_number", None)
                else:
                    package.callback(f"You have {bulls} bulls and {cows} cows")
        else:
            number = ""
            while len(number) < 4:
                digit = random.choice("0123456789")
                if len(number) == 0 and digit != "0":
                    number += digit
                    continue
                if digit in number:
                    continue
                number += digit
            package.conversation.data["bull_number"] = number
            package.callback("Guess 4 digit number")
