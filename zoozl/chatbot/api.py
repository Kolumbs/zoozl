"""API for extending chat interface.

Extension module should contain as a minimum one subclass of Interface
"""

import base64
import datetime
import uuid

import dataclasses
from dataclasses import dataclass


@dataclass
class MessagePart:
    """Contains one single atomic communication piece between talker and bot.

    A Message will contain one or more MessageParts.
    """

    text: str = ""
    binary: bytes = dataclasses.field(
        default=b"", metadata={"encode": lambda x: base64.b64encode(x).decode()}
    )
    media_type: str = ""  # e.g text/plain, image/jpeg, application/json


@dataclass
class Message:
    """Message object to be exchanged between talker and bot.

    author - the talker who sent the message (e.g. user, bot)
    parts - list of MessagePart objects
    """

    parts: list = dataclasses.field(
        default_factory=list,
        metadata={"encode": lambda x: [encode_class(i) for i in x]},
    )
    author: str = ""
    sent: datetime = dataclasses.field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        metadata={"encode": lambda x: x.isoformat()},
    )

    def __post_init__(self):
        """Upload parts as MessageParts."""
        if isinstance(self.parts, str):
            self.parts = [MessagePart(self.parts)]
        else:
            self.parts = [MessagePart(part) for part in self.parts]
        if isinstance(self.sent, str):
            self.sent = datetime.datetime.fromisoformat(self.sent)

    @property
    def text(self):
        """Return text part of the message."""
        return " ".join([part.text for part in self.parts])


def encode_messages(messages):
    """Encode messages."""
    return [encode_class(i) for i in messages]


def encode_class(message):
    """Encode dataclass."""
    result = {}
    for i in dataclasses.fields(message):
        if i.metadata.get("encode"):
            result[i.name] = i.metadata["encode"](getattr(message, i.name))
        else:
            result[i.name] = getattr(message, i.name)
    return result


@dataclass
class Conversation:
    """Conversation with people(talkers) who request actions.

    There can be many conversations for one talker, but preferably only one ongoing per
    talker at a time.
    """

    uuid: str = dataclasses.field(default="", metadata={"key": True})
    talker: str = ""
    ongoing: bool = False
    subject: str = ""
    messages: list = dataclasses.field(
        default_factory=list, metadata={"encode": encode_messages}
    )
    data: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Generate uuid automatically if not provided."""
        if not self.uuid:
            self.uuid = str(uuid.uuid4())


@dataclass
class Package:
    """Package contains information data that is exchanged between bot and commands.

    conversation - saveable state of conversation between user and chatbot
    callback - a function to allow sending back Message object to user
        (as a convenience it is possible to send just text string that will be
        formatted into Message object automatically by interface)
    """

    conversation: Conversation
    callback: type

    @property
    def last_message_text(self):
        """Retrieve latest text from conversation."""
        if self.conversation.messages:
            last_message = self.conversation.messages[-1]
            return last_message.text


class Interface:
    """Interface to the chat command handling.

    Subclass this to extend a chat module

    aliases - define a set of command functions that would trigger this event
    """

    # Command names as typed by the one who asks
    aliases = set()

    def load(self, root):
        """Preload once an Interface.

        :params root: interface root object
        """

    def consume(self, context, package):
        """Handle all requests when subject is triggered.

        :param context: InterfaceMap object that allows to communicate with other
            interfaces available apart from other things
        :param package: is a special object defined as Package, exchanges data
        """

    def is_complete(self):
        """Must return True or False."""
        return False
