"""Tests on email handler in zoozl server.

Module provides end-to-end testing for email. The flow of testing is as follows:

    1. Email message is sent to LMTP destination.
    3. LMTP destination is zoozl server listening on localhost (fixtures.zoozl_server).
    4. Zoozl server handles received message over LMTP port.
    5. Zoozl server handles email and sends back email message to SMTP server.
    6. Message is stored as response messages in SMTP Server (fixtures.smtp_server).

Actors:
    SMTP server (fixtures.smtp_server)
    Zoozl server (fixtures.zoozl_server)
"""

import asyncio
import email
from smtplib import LMTP

from zoozl import chatbot, emailer

from tests import base as bs
from tests.fixtures import smtp_server, zoozl_server


def setUpModule():
    """Boot zoozl server in background."""
    zoozl_server.configure(config_file="tests/data/ping.toml")


def tearDownModule():
    """Terminate zoozl server."""
    zoozl_server.terminate()


class EmailHandler(smtp_server.AsyncMessage):
    """Handles incoming and outgoing email messages.

    When email is sent to receiver it is forwarded to LMTP port, when email is sent to
    sender it is stored within object `messages` array.
    """

    def __init__(
        self, receiver_email: str, receiver_port: int, sender_email: str, messages: list
    ):
        """Initialize message handler."""
        self.receiver_email = receiver_email
        self.receiver_port = receiver_port
        self.sender_email = sender_email
        self.received_messages = messages
        super().__init__()

    async def handle_message(self, message: email.message.Message):
        """Handle email message."""
        if message["to"] == self.receiver_email:
            await self.forward_to_lmtp(message)
        elif message["to"] == self.sender_email:
            self.received_messages.append(message)
        else:
            raise ValueError(f"Unknown recipient {message['to']}")

    async def forward_to_lmtp(self, message: email.message.Message):
        """Forward message to LMTP server."""
        with LMTP(host="localhost", port=self.receiver_port) as lmtp:
            lmtp.send_message(message, message["from"], message["to"])


class Email(bs.AbstractServer):
    """Testcases on email handler."""

    lmtp_port = 30002
    smtp_port = 8090
    sender = "zoozl.sender@zoozl.local"
    receiver = "zoozl.receiver@zoozl.local"

    async def asyncSetUp(self):
        """Set up smtp server."""
        self.email_messages = []
        await super().asyncSetUp()
        self.server = await smtp_server.start_server(
            self.smtp_port,
            EmailHandler(
                self.receiver, self.lmtp_port, self.sender, self.email_messages
            ),
        )

    async def asyncTearDown(self):
        """Tear down smtp server."""
        self.server.close()
        await self.server.wait_closed()
        await super().asyncTearDown()

    async def send_email(self, subject, msg):
        """Send email message."""
        await emailer.send(
            self.sender, self.receiver, subject, msg, port=self.smtp_port
        )

    async def assert_email_received(self, subject, msg):
        """Check if email was received."""
        wait = 0
        while not self.email_messages and wait < 10:
            await asyncio.sleep(0.1)
            wait += 1

    async def test(self):
        """Test email message."""
        subject = "Need to make enquiry"
        text = "Ābece"
        msg = chatbot.Message(text)
        await self.send_email(subject, msg)
        await self.assert_email_received(subject, msg)
        self.assertEqual(len(self.email_messages), 1)
        message = self.email_messages[0]
        self.assertEqual(message["subject"], "Re: " + subject)
        self.assertEqual(message["from"], self.sender)
        for part in message.walk():
            self.assertEqual(text, message.get_payload().strip())
