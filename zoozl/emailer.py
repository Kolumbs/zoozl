"""Email sending services."""

import asyncio
import email.message
from smtplib import SMTP

from . import chatbot


def _send_email_msg(msg: email.message.Message, port) -> None:
    """Send 'msg' to smtp server."""
    with SMTP(host="localhost", port=port) as smtp:
        smtp.send_message(msg, msg["from"], msg["to"])


async def send(
    sender: str, receiver: str, subject: str, msg: chatbot.Message, port=25
) -> None:
    """Send email message."""
    mail = email.message.EmailMessage()
    mail["from"] = sender
    mail["to"] = receiver
    mail["subject"] = subject
    txt = ""
    for part in msg.parts:
        if part.binary:
            maintype, subtype = part.media_type.split("/", maxsplit=1)
            mail.add_attachment(
                part.binary,
                maintype=maintype,
                subtype=subtype,
                filename=part.filename,
            )
        else:
            txt += part.text
    mail.set_content(txt)
    await asyncio.to_thread(_send_email_msg, mail, port=port)


def send_sync(sender: str, receiver: str, subject: str, msg: chatbot.Message, port=25):
    """Send email message in sync mode."""
    loop = asyncio.get_running_loop()
    loop.create_task(send(sender, receiver, subject, msg, port))


def serialise_email_message(msg: email.message.Message) -> chatbot.Message:
    """Serialise email message into chatbot Message."""
    for part in msg.walk():
        if part.get_content_maintype() == "text":
            return chatbot.Message(part.get_payload(decode=True).decode())
