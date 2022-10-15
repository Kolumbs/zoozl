"""Module defines chat subject commands"""
import dataclasses as data
from dataclasses import dataclass

from chat import process

@dataclass
class Interface():
    """Interface to the chat command handling"""
    required: set = data.field(default_factory=set)
    optional: set = data.field(default_factory=set)
    attachment: bool = False
    # must contain callables that accept text and conversation memory item, if non empty
    # allows to intercept certain text to add, remove or augment requirements
    auxiliaries: set = data.field(default_factory=set)


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
