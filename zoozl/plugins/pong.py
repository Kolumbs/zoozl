"""Ping pong plugin.

Sends the same message it receives back
"""

from zoozl.chatbot import Interface


class PingPong(Interface):
    """Ping pong messaging."""

    aliases = {"help"}

    def consume(self, context, package):
        """Send always back whatever received."""
        package.conversation.subject = "greet"
        package.callback(package.last_message_text)
