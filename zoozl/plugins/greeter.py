"""Example plugin that sends always greeting message."""

from zoozl.chatbot import Agent as BaseAgent


class Agent(BaseAgent):
    """Greeter single agent."""

    async def greet(self, package):
        """Greet on connect."""
        if package.conversation.ongoing:
            package.callback("Hey. What would you like me to do?")
        else:
            package.callback("Hello!")
            msg = "I can do few things. Ask me for example "
            msg += "to play games or something."
            package.callback(msg)
            package.conversation.ongoing = True

    async def consume(self, package):
        """Greet the user."""
        package.callback("Hello!")
