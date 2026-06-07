"""Ping pong single agent."""

from zoozl.chatbot import Agent as BaseAgent


class Agent(BaseAgent):
    """Ping pong messaging."""

    async def consume(self, package):
        """Send always back whatever received."""
        package.callback(package.last_message_text)
