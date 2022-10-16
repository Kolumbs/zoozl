"""Module defines chat subject commands"""
# pylint: disable=all
import dataclasses as data
from dataclasses import dataclass

from chat import process


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
    self._clean()

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

def action(self):
    """checks if ready for action, if so executes otherwise asks info"""
    if self.is_complete():
        self.perform()
    else:
        self.ask_missing()


def do_add_expense():
    """defines add expense subject requirements"""
    return Interface(
        required = {"date", "reference", "comment", "partner", "value"},
        optional = {"expense_account", "currency", "split"},
        attachment = True,
        auxiliaries = {allow_no_attachment,}
    )

def do_private_expense():
    """private expense"""
    return Interface(
        required = {"date", "partner", "value"},
    )

def do_get_help():
    """defines help requirements"""
    return Interface()

def do_get_outstanding():
    """defines report requirements"""
    return Interface()

def do_create_partner():
    """defines partner requirements"""
    return Interface(
        required = {"name"},
        optional = {"other_names"},
    )

def allow_no_attachment(text, talk):
    """support function to drop attachment requirement"""
    cmds = ["no attachment", "without attachment", "skip attachment", "drop attachment"]
    pos = process.extractOne(text, cmds)
    if pos[1] > 98:
        talk.attachment = b'Attachment explicitly skipped'
        return "Skipping attachment"
    return ""

def do_upwork_invoices():
    """upwork invoice upload"""
    return Interface(
        attachment = True,
    )

def do_get_ledger():
    """full ledger report in excel"""
    return Interface(
        required = {"filter_by_quarter"},
    )

def do_update_ledger():
    """manual ledger update"""
    return Interface(
        attachment = True,
    )
