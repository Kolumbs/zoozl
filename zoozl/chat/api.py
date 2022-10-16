"""API for extending chat interface"""
import dataclasses
from dataclasses import dataclass


@dataclass
class Message():
    """Communication piece between talker and bot"""
    text: str = ''
    binary: bytes = b''


@dataclass
class Conversation():
    """
    Conversations with people(talkers) who request actions
    """
    talker: str = dataclasses.field(default=None, metadata={"key": True})
    ongoing: bool = False
    subject: str = ""
    data: dict = dataclasses.field(default_factory=dict)
    attachment: bytes = b''


@dataclass
class Package:
    """
    Package contains information data that is exchanged between bot and commands
    """
    message: Message
    conversation: Conversation
    callback: type


class Interface():
    """Interface to the chat command handling"""
    # Command names as typed by the one who asks
    aliases = set()

    def __init__(self, conf):
        """interface receives global conf when initialised"""
        self.conf = conf

    def consume(self, package):
        """function that handles all requests when subject is triggered"""

    def is_complete(self):
        """must return True or False"""
        return True
