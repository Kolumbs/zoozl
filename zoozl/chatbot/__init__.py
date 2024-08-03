"""Package that allows to build and extend chatbot.

Usage:
    -> interface.Chat or just Chat to interact with bot
        With the interface.Chat additional extension modules are loaded
    -> api for extending ChatBot
        With the api help classes extension modules are built
"""

from .api import Interface, Message, Conversation, Package
from .interface import Chat


__all__ = ["Interface", "Message", "Conversation", "Package", "Chat"]
