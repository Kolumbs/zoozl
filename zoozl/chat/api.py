"""API for extending chat interface

Extension module should contain as a minimum one subclass of Interface
"""
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

    message - a Message object received from the user to chatbot
    conversation - saveable state of conversation between user and chatbot
    callback - a function to allow sending back Message object to user
        (as a convenience it is possible to send just text string that will be
        formatted into Message object automatically by interface)
    """
    message: Message
    conversation: Conversation
    callback: type


class Interface():
    """Interface to the chat command handling

    Subclass this to extend a chat module

    aliases - define a set of command functions that would trigger this event
    """
    # Command names as typed by the one who asks
    aliases = set()

    def __init__(self, conf):
        """interface receives global conf when initialised"""
        self.conf = conf

    def consume(self, package):
        """function that handles all requests when subject is triggered
        package - is a special object defined as Package and is the exchange data package
        """

    def is_complete(self):
        """must return True or False"""
        return True
