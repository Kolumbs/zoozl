"""Module defines common chat subject commands"""
import random

from rapidfuzz import process

from .api import Interface, Message


class Help(Interface):
    """defines helper constructor for chat"""
    aliases = {"do get help", "help"}

    def consume(self, package):
        cmds = []
        for i in self.conf["interfaces"].keys():
            if i in Help.aliases or i in Hello.aliases:
                continue
            cmds.append(i)
        msg = "\n".join(cmds)
        msg = "Try asking:\n" + msg
        package.callback(msg)


class Hello(Interface):
    """defines hello commands"""
    aliases = {"hello", "hi", "how are you", "hey"}

    def consume(self, package):
        greets = ["Hello", "Hey", "Hello, hello. What do you want to do?"]
        package.callback(random.choice(greets))


def count_bulls_cows(challenge, number):
    """counts bulls and cows"""
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


class Games(Interface):
    """defines games"""
    aliases = {"play games"}
    complete = False

    def is_complete(self):
        return self.complete

    def consume(self, package):
        if "game" not in package.conversation.data:
            self.get_game(package)
        else:
            getattr(self, package.conversation.data["game"])(package)

    def get_game(self, package):
        """try to get game name or ask for it"""
        games = {
            "bull": "bull_game",
            "bulls and cows": "bull_game",
            "bulls & cows": "bull_game",
            "yes": "bull_game",
        }
        game = process.extractOne(package.message.text.lower(), games.keys())
        if game[1] >= 95:
            package.conversation.data["game"] = games[game[0]]
            package.callback("OK. Let's play bulls and cows")
            self.bull_game(package)
        else:
            package.callback(Message("what game you want to play? bulls and cows?"))

    def bull_game(self, package):
        """play a number guessing game"""
        if "bull_number" in package.conversation.data:
            number = str(package.message.text)
            if len(number) != 4:
                package.callback(Message("Give number with exactly 4 digits"))
            elif len(set(number)) != len(number):
                package.callback("Digits must be unique in number")
            else:
                bulls, cows = count_bulls_cows(
                    number,
                    package.conversation.data["bull_number"]
                )
                if bulls == 4:
                    package.callback("Congrats. You guessed right")
                    self.complete = True
                else:
                    package.callback(f"You have {bulls} bulls and {cows} cows")
        else:
            number = ""
            while len(number) < 4:
                digit = random.choice("0123456789")
                if len(number) == 0 and digit != '0':
                    number += digit
                    continue
                if digit in number:
                    continue
                number += digit
            package.conversation.data["bull_number"] = number
            package.callback("Guess 4 digit number")
