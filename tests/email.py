"""Tests on email handler in zoozl server.

Module provides end-to-end testing for email. The flow of testing is as follows:

    1. Email message is sent to SMTP server (must be running on local system).
    2. Message must be sent to LMTP destination by SMTP server.
    3. LMTP destination is zoozl server listening on localhost.
    4. Zoozl server handles received message over LMTP port.
    5. Zoozl server handles email and sends back email message to SMTP server.
    6. Message is sent to LMTP destination listening for results from SMTP server.

Actors:
    SMTP server
    A smtp server that must be installed on the system and running with configuration to
    accept two email users zoozl.sender@zoozl.local and zoozl.receiver@zoozl.local
    When email is sent to zoozl.sender@zoozl.local it should be forwarded to LMTP
    destinations at 8090 local port, and when email is sent to zoozl.receiver@zoozl.local
    then it should be forwarded to LMTP destination at 8091 local port.

    Example for smtpd daemon configuration:
    ```
    # smtpd.conf
    action zoozl_receive lmtp localhost:8090
    action zoozl_send lmtp localhost:8091
    match for rcpt-to "zoozl.receiver@zoozl.local" action zoozl_receive
    match for rcpt-to "zoozl.sender@zoozl.local" action zoozl_send
    ```

    Zoozl server
    Listening on LMTP port 8090, it is started before tests.

    LMTP result destination
    Socket listening on localhost port 8091, it collects email messages sent back by
    Zoozl server.
"""

from zoozl import chatbot, email

from tests import base as bs
from tests.fixtures import smtp_server


class Email(bs.AbstractServer):
    """Testcases on email handler."""

    config_file = "tests/data/email.toml"
    sender = "zoozl.sender@zoozl.local"
    receiver = "zoozl.receiver@zoozl.local"

    async def send_email(self, subject, msg):
        """Send email message."""
        await email.send(self.sender, self.receiver, subject, msg)

    def assert_email_received(self, subject, msg):
        """Check if email was received."""

    @bs.unittest.skip("Not implemented")
    async def test(self):
        """Test email message."""
        subject = "Need to make enquiry"
        text = "Ābece"
        msg = chatbot.Message(text)
        await self.send_email(subject, msg)
        self.assert_email_received(subject, msg)
