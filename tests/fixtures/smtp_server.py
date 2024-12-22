"""SMTP server.

Example usage:
>>> from tests.fixtures import smtp_server
>>> class MessageHandler(smtp_server.TwoWayMessage):
...     async def handle_message(self, message: email.message.Message):
...         print(message)
>>> server = await smtp_server.start_server(port=25, handler=MessageHandler)
>>> # Run tests that interact with smtp server on given port
>>> # Observe your custom handler handling received messages
>>> # Gracefully shutdown server
>>> server.close()
>>> server.abort_clients()
>>> await server.wait_closed()

Usual setup in testcase module:
    ```python
    from unittest import IsolatedAsyncioTestCase

    from tests.fixtures import smtp_server

    class MyTestCase(IsolatedAsyncioTestCase):

        async def asyncSetUp(self):
            self.server = await smtp_server.start_server()

        async def asyncTearDown(self):
            self.server.close()
            self.server.abort_clients()
            await self.server.wait_closed()

        def test_something(self):
            self.send_email()
            self.assertTrue(await self.server.get_emails())
    ```

A smtp server fixture is a valid SMTP server, it handles emails within email
handling protocol.
Accepts two email users RECEIVER_EMAIL and SENDER_EMAIL, when email is sent to
RECEIVER_EMAIL it is forwarded to RECEIVER_PORT as LMTP destination. When email is
sent to SENDER_EMAIL it is stored within server and accessible over get_emails coroutine.
"""

import asyncio
import functools

from aiosmtpd.smtp import SMTP
from aiosmtpd.handlers import AsyncMessage

from tests.fixtures import network


async def start_server(port: int, handler: AsyncMessage):
    """Start smtp server that immediately listens on port.

    handler: AsyncMessage instance that handles received emails.
    """
    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        functools.partial(SMTP, handler, loop=loop),
        port=port,
    )
    try:
        network.socket_check(port)
    except Exception:
        server.close()
        await server.wait_closed()
        raise
    return server
