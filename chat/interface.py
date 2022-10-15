"""
Main chat interface that external modules interact with

>>> def callback(message):
        print(message.text)
>>> chat.Chat("unique_talker_id", callback)
>>> chat.greet()
>>> chat.send(chat.Message("Hello"))
"""
from dataclasses import dataclass


@dataclass
class Message():
    """Communication piece between talker and chat"""
    text: str = ''
    binary: bytes = b''


@dataclass
class Conversation():
    """
    Conversations with people(talkers) who request actions
    """
    talker: str = data.field(default=None, metadata={"key": True})
    ongoing: bool = False
    subject: str = ""
    data: dict = data.field(default_factory=dict)
    attachment: bytes = b''


@dataclass
class ChatSubjectLookup():
    """
    Subject lookup from chat messages
    """
    cmd: str
    sentence: str


class Chat():
    """Interface for communication and routing with talker"""

    def __init__(self, talker, callback, path=None, conf=None):
        """
        Initialise comm interface with talker
        """
        self._m = membank.LoadMemory(path)
        self._t = self._m.get.conversation(talker=talker)
        if not self._t:
            self._t = memories.Conversation(
                talker = talker,
            )
        self._call = callback
        self._conf = conf
        self._interface = chat_interface.Interface()
        self._interface_ready = self._load_interface()

    def greet(talker, text, files, callback, conf):
        "Hello! I am bot and I represent company that made me and can make others similar to me."
        "I can do few things. You can ask me for example to play games or do accounting"

    def send(talker, text, files, callback, conf):
        """make conversation by receiving text and sending message back via callback"""
        talk = Chat(talker, conf, callback)
        if talk.ongoing:
            if talk.subject:
                talk.do_subject(text, files)
                talk.action()
            else:
                if not talk.get_subject(text):
                    callback("I didn't get. Would you like me to send full list of commands?")
                    talk.set_subject("do_get_help")
                else:
                    talk.action()
        else:
            talk.ongoing = True
            if not talk.get_subject(text):
                callback("What would you like me to do?")
            else:
                talk.action()

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

    def action(self):
        """checks if ready for action, if so executes otherwise asks info"""
        if self.is_complete():
            self.perform()
        else:
            self.ask_missing()

    def get_subject(self, text):
        """tries to understand subject from text
        if understood sets the subject and returns it
        otherwise returns None
        """
        subj = self._m.get.chatsubjectlookup(sentence=text)
        if subj:
            self.set_subject(subj.cmd)
        else:
            cmd_list = [" ".join(i.split("_")) for i in brain.generate_cmd_list()]
            pos = process.extractOne(text, cmd_list)
            if pos[1] >= 95:
                cmd = pos[0].replace(" ", "_")
                self._m.put(memories.ChatSubjectLookup(cmd, text))
                subj = cmd
                self.set_subject(subj)
        return subj

    def set_subject(self, cmd):
        """sets subject as per cmd"""
        self._t.subject = cmd
        self._m.put(self._t)
        self._interface_ready = self._load_interface()

    def clear_subject(self):
        """resets conversation to new start"""
        self.set_subject("")
        self._call("OK. Let's start over. I have saved however what you sent me before just in case")

    def do_subject(self, text, attach):
        """continue on the subject"""
        if self._positive(text):
            self._load_data(text, attach[0])

    def _positive(self, text):
        """assert that text seems positive otherwise cancels the subject"""
        choices = ["no", "cancel", "stop", "stop it", "forget", "start again", "naah"]
        pos = process.extractOne(text, choices)
        if pos[1] > 97:
            self.clear_subject()
            return False
        return True

    def _load_data(self, text, attachment):
        """loads text and attachment as per subject interface"""
        auxes = False
        if self._interface.auxiliaries:
            for support in self._interface.auxiliaries:
                answer = support(text, self._t)
                if answer:
                    self._call(answer)
                    self._m.put(self._t)
                    auxes = True
                    break
        if auxes: return
        try:
            data = handlers.get_json(text)
        except RuntimeWarning as err:
            self._call(err)
        if attachment and self._interface.attachment:
            self._t.attachment = attachment
            self._m.put(self._t)
        elif attachment:
            self._call("I don't need attachment so I ignore it")
        fields = self._interface.required.union(self._interface.optional)
        if len(data) > 1:
            self._call("Sorry not more than invoice. Do not duplicate fields")
        elif len(data) == 1:
            data = data[0]
            for key in data:
                if key in fields:
                    self._t.data[key] = data[key]
                    self._m.put(self._t)
                else:
                    self._call(f"Field '{key}' is not valid, ignoring")

    def _load_interface(self):
        """
        loads interface demands
        marks internal flag if succesfull
        """
        if not self._t.subject:
            return False
        if self._t.subject not in dir(chat_interface):
            msg = f"Ups. I am confused, don't know what to do with '{self._t.subject}'"
            self._call(msg)
            return False
        interface = getattr(chat_interface, self._t.subject)
        self._interface = interface()
        return True

    def is_complete(self):
        """checks if subject interface is complete and ready to pass on"""
        if not self._interface_ready:
            return False
        keys = self._t.data.keys()
        for req in self._interface.required:
            if req not in keys:
                return False
        return self._interface.attachment == bool(self._t.attachment)

    def perform(self):
        """performs a task"""
        msg, attach, fname = brain.do_task(
            self._conf,
            self._m,
            self._t.subject,
            [self._t.data],
            self._t.attachment,
        )
        self._call(msg, attach, fname)
        self._t.subject = ""
        self._t.attachment = b''
        self._t.data = {}
        self._m.put(self._t)

    def ask_missing(self):
        """sends missing data requirements"""
        msg = ""
        keys = self._t.data.keys()
        mand = []
        for req in self._interface.required:
            if req not in keys:
                mand.append(req)
        attach = self._interface.attachment == bool(self._t.attachment)
        opts = []
        for opt in self._interface.optional:
            if opt not in keys:
                opts.append(opt)
        if mand:
            msg += "I miss fields: " + ", ".join(mand)
        if opts:
            if msg:
                msg += "\n"
            msg += "Optional fields: " + ", ".join(opts)
        if not attach:
            if msg:
                msg += "\n"
            msg += "I need attachment"
        if msg:
            self._call(msg)
