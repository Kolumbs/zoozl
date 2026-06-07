"""Package that allows to build and extend chatbot.

Usage:
    -> interface.Chat or just Chat to interact with bot
        With the interface.Chat additional extension modules are loaded
    -> api for extending ChatBot
        With the api help classes extension modules are built
"""

from .api import Agent, Interface, Message, Conversation, Package, MessagePart
from .interface import Chat, InterfaceRoot


__all__ = [
    "Chat",
    "Agent",
    "Conversation",
    "Interface",
    "InterfaceRoot",
    "Message",
    "Package",
    "MessagePart",
]
