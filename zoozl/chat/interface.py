"""
Main chat interface that external modules interact with

>>> def callback(message):
        print(message.text)
>>> bot = chat.Chat("unique_talker_id", callback)
>>> bot.greet()
>>> bot.ask(chat.Message("Hello"))
>>> bot.close() # Important to call this, to close any resources opened related to memory
"""
import membank
from rapidfuzz import process

from . import helpers
from .api import Interface, Message, Conversation, Package


# pylint: disable=too-many-instance-attributes, too-many-arguments
class Chat():
    """Interface for communication and routing with talker"""

    def __init__(self, talker, callback, interfaces=tuple(), path=None, conf=None):
        """
        Initialise comm interface with talker, one instance per talker

        Talker must be something unique. This will serve as identification
        across several talkers that might turn to bot for chat.

        Callback must be a callable that accepts Message as only argument

        If path is not set, Chat instance will hold memories of ongoing chats
        with talker only in the instance itself, closing instance will render all previous
        conversations forgotten. In such cases Chat instance per talker should be
        kept alive as long as possible. if path is set, it must lead to valid path
        for Chat instance to be able to store it's persistent memory, then
        history of talker conversations will be preserved upon instance destructions.

        Conf is optional pass-through dictionary for any commands that require system wide
        configuration. By default includes set of available interfaces in key 'interfaces'

        Interfaces are additional modules that are supported by chat and to be installed
        """
        self._m = membank.LoadMemory(path)
        self._t = self._m.get.conversation(talker=str(talker))
        if not self._t:
            self._t = Conversation(
                talker = str(talker),
            )
        self._callback = callback
        if conf and "interfaces" in conf:
            raise RuntimeError("Name 'interfaces' is reserved and can't be used in conf")
        self._conf = conf if conf else {}
        self._commands = {}
        interfaces += (helpers, )
        for i in interfaces:
            self.load_interface(i)
        self._conf['interfaces'] = self._commands

    def close(self):
        """when membank supports close this should close it"""
        # self._m.close()

    def greet(self):
        """send first greeting message"""
        if self.ongoing:
            self._call("Hey. What would you like me to do?")
        else:
            msg = "Hello! I am bot and I represent company "
            msg += "that made me and can make others similar to me."
            self._call(msg)
            msg = "I can do few things. Ask me for example "
            msg += "to play games or do accounting."
            self._call(msg)
            self.ongoing = True

    def ask(self, message):
        """make conversation by receiving text and sending message back via callback"""
        if self.ongoing:
            if self.subject:
                self.do_subject(message)
            else:
                if not self.get_subject(message):
                    self._call("I didn't get. Would you like me to send full list of commands?")
                    self.set_subject("do get help")
                else:
                    self.do_subject(message)
        else:
            self.ongoing = True
            if not self.get_subject(message):
                self._call("What would you like me to do?")
            else:
                self.do_subject(message)

    @property
    def talker(self):
        """returns talker"""
        return self._t.talker

    @property
    def ongoing(self):
        """checks if talk is ongoing"""
        return self._t.ongoing

    @ongoing.setter
    def ongoing(self, value):
        """sets talk ongoing value"""
        self._t.ongoing = value
        self._m.put(self._t)

    @property
    def subject(self):
        """return subject if present"""
        return self._t.subject

    def load_interface(self, interface):
        """load additional supported commands into chat interface"""
        for i in dir(interface):
            obj = getattr(interface, i)
            if isinstance(obj, type) and issubclass(obj, Interface):
                obj = obj(self._conf)
                for cmd in obj.aliases:
                    if cmd in self._commands:
                        raise RuntimeError(f"Clash of interfaces! '{cmd}' already loaded")
                    self._commands[cmd] = obj

    def get_subject(self, message):
        """tries to understand subject from message
        if understood sets the subject and returns it
        otherwise returns None
        """
        pos = process.extractOne(message.text.lower(), self._commands.keys())
        message.text = "" # So that next consumer does not have it
        if pos and pos[1] >= 90:
            self.set_subject(pos[0])
            return pos[0]
        return None

    def set_subject(self, cmd):
        """sets subject as per cmd"""
        self._t.subject = cmd
        self._m.put(self._t)

    def clear_subject(self):
        """resets conversation to new start"""
        self._call("OK. Let's start over.")
        self._clean()

    def do_subject(self, message):
        """continue on the subject"""
        if self._positive(message.text):
            package = Package(message, self._t, self._call)
            self._commands[self._t.subject].consume(package)
            self._m.put(package.conversation)
        if self._t.subject and self._commands[self._t.subject].is_complete():
            self._clean()

    def _call(self, message):
        """constructs Message and routes it to callback
        It must be either simple string text or Message object"""
        if not isinstance(message, Message):
            message = Message(message)
        self._callback(message)

    def _positive(self, text):
        """assert that text seems positive otherwise cancels the subject"""
        choices = ["no", "cancel", "stop", "stop it", "forget", "start again", "naah"]
        pos = process.extractOne(text, choices)
        if pos[1] > 97:
            self.clear_subject()
            return False
        return True

    def _clean(self):
        """clean all data in conversation to initial state"""
        self._t.subject = ""
        self._t.attachment = b''
        self._t.data = {}
        self._m.put(self._t)
