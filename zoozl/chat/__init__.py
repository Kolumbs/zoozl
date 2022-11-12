"""Module that allows to build and extend chatbot

Usage:
    -> interface.Chat or just Chat to interact with bot
        With the interface.Chat additional extension modules are loaded
    -> api for extending ChatBot
        With the api help classes extension modules are built
"""
import membank

from .api import Interface, Message, Conversation, Package
from .interface import Chat
