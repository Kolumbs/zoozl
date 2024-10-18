"""Zoozl server.

Meant to be run in main python thread.

>>> with open("conf.toml", "rb") as file:
...     conf = tomllib.load(file)
>>> # Run server until interrupted
>>> start(conf)
"""

from abc import abstractmethod
import asyncio
import functools
import json
import logging
import signal
import traceback
import uuid

from zoozl import websocket, chatbot


log = logging.getLogger(__name__)

signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))


HTTP_STATUS_CODES = (
    (200, "OK"),
    (400, "Bad Request"),
    (405, "Method Not Allowed"),
    (408, "Request Timeout"),
    (414, "URI Too Long"),
    (500, "Internal Server Error"),
    (501, "Not Implemented"),
)


async def send_http_response(writer: asyncio.StreamWriter, status: int, **headers):
    """Send HTTP response to writer."""
    if "connection" not in headers:
        headers["connection"] = "close"
    try:
        reason = next(msg for code, msg in HTTP_STATUS_CODES if code == status)
    except StopIteration:
        raise NotImplementedError(f"Invalid status code: {status}")
    writer.write(f"HTTP/1.1 {status} {reason}\r\n".encode("ascii"))
    for key, value in headers.items():
        writer.write(f"{key}: {value}\r\n".encode("ascii"))
    writer.write(b"\r\n")
    await writer.drain()


class HTTPRequest:
    """Message container for receiving HTTP/1.1 compliant messages.

    Example usage:

        >>> msg = HTTPRequest(reader, writer)
        >>> if await asyncio.wait_for(msg.read(), timeout=1):
        >>>     print(msg.method)
        >>>     print(msg.request_uri)
        >>>     print(msg.headers)
        >>>     # reader still contains message body
        >>>     # writer is still open and has not sent back any response
        >>> else:
        >>>     # reader might still be able to read some data
        >>>     # writer has sent back error message as per HTTP/1.1
        >>>     # writer must be closed as `connection: close` header was sent to client
        >>>     print(msg.error_code)
        >>>     print(msg.error_message)
        >>> # Responsibility of closing writer is on the caller
        >>> writer.close()
        >>> await writer.wait_closed()

    The `read()` method reads from the reader and parses the message up to the message
    body, consuming the following:

        - Start-line: [CONSUMED]
        - *( header-field CRLF ): [CONSUMED]
        - CRLF: [CONSUMED]
        - Message body: [NOT CONSUMED]

    method (str): HTTP method used in the request, not guaranteed to be valid HTTP method
    request_uri (str): URI requested
    headers (dict): headers in the request
    """

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Initialise HTTP message with empty attributes."""
        self.method = None
        self.request_uri = None
        self.headers = None
        self.error_code = None
        self.error_message = None
        self.reader = reader
        self.writer = writer

    async def read(self):
        """Read from reader and parse HTTP message."""
        if not await self._read_request_line():
            return False
        if not await self._read_headers():
            return False
        return True

    async def _read_method(self):
        """Read method from reader."""
        error_code = None
        try:
            method = await self.reader.readuntil(b" ")
            method = method[:-1]
        except asyncio.LimitOverrunError:
            error_code = 501
            self.error_message = "While reading method, buffer limit exceeded"
        except asyncio.IncompleteReadError:
            error_code = 400
            self.error_message = "While reading method, incomplete read"
        else:
            try:
                self.method = method.decode("ascii")
            except UnicodeError:
                error_code = 400
                self.error_message = "While decoding method, invalid ascii"
            else:
                return True
        await send_http_response(self.writer, error_code)
        self.error_code = error_code
        return False

    async def _read_request_uri(self):
        """Read request-uri from reader."""
        error_code = None
        try:
            request_uri = await self.reader.readuntil(b" ")
            request_uri = request_uri[:-1]
        except asyncio.LimitOverrunError:
            error_code = 414
            self.error_message = "While reading request-uri, buffer limit exceeded"
        except asyncio.IncompleteReadError:
            error_code = 400
            self.error_message = "While reading request-uri, incomplete read"
        else:
            try:
                self.request_uri = request_uri.decode("ascii")
            except UnicodeError:
                error_code = 400
                self.error_message = "While decoding request-uri, invalid ascii"
            else:
                return True
        await send_http_response(self.writer, error_code)
        self.error_code = error_code
        return False

    async def _read_version(self):
        """Read version from reader."""
        error_code = None
        try:
            await self.reader.readuntil(b"\r\n")
        except (asyncio.LimitOverrunError, asyncio.IncompleteReadError):
            error_code = 400
            self.error_message = (
                "While reading version, buffer limit exceeded or incomplete read"
            )
        else:
            return True
        await send_http_response(self.writer, error_code)
        self.error_code = error_code
        return False

    async def _read_request_line(self):
        """Read first line from reader."""
        for block in [self._read_method, self._read_request_uri, self._read_version]:
            if not await block():
                return False
        return True

    async def _read_headers(self):
        """Read headers from reader."""
        error_code = None
        try:
            headers = await self.reader.readuntil(b"\r\n\r\n")
            headers = headers[:-4]
        except (asyncio.LimitOverrunError, asyncio.IncompleteReadError):
            error_code = 400
            self.error_message = (
                "While reading headers, buffer limit exceeded or incomplete read"
            )
        else:
            try:
                headers = headers.decode("ascii")
            except UnicodeError:
                error_code = 400
                self.error_message = "While decoding headers, invalid ascii"
            try:
                headers = headers.split("\r\n")
                self.headers = dict(
                    # keys are case-insensitive and values are stripped of spaces
                    (key.lower(), value.strip())
                    for key, value in map(lambda x: x.split(":", maxsplit=1), headers)
                )
            except ValueError as e:
                error_code = 400
                self.error_message = f"While decoding headers, invalid format: {e}"
            else:
                return True
        await send_http_response(self.writer, error_code)
        self.error_code = error_code
        return False


async def run_servers_stacked(*servers):
    """Run servers in stacked manner.

    Last server is runs forever, while others are started in stack.
    """
    if len(servers) < 1:
        log.error("No servers configured to run")
    elif len(servers) < 2:
        async with servers[0]:
            await servers[0].serve_forever()
    else:
        async with servers[0]:
            await run_servers_stacked(*servers[1:])


def http_request(coroutine):
    """Handle HTTP request message and pass it to coroutine."""

    @functools.wraps(coroutine)
    async def wrapper(self, reader, writer):
        msg = HTTPRequest(reader, writer)
        try:
            if await asyncio.wait_for(msg.read(), 3):
                await coroutine(self, reader, writer, msg)
            else:
                log.warning("Rejected HTTP message: %s", msg.error_message)
                return
        except asyncio.TimeoutError:
            log.warning("HTTP message read timed out")
            try:
                await send_http_response(writer, 408)
            except ConnectionError:
                pass
        except ConnectionError:
            pass
        except Exception as e:
            log.error("".join(traceback.format_exception(e)))
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    return wrapper


async def websocket_request(reader, writer, msg: HTTPRequest):
    """Handle websocket requests."""


async def slack_request(*args, **kwargs):
    """Handle slack requests."""


class RequestHandler:
    """Allows to handle requests from different sources."""

    def __init__(self, root: chatbot.InterfaceRoot):
        """Initialise with interface root.

        :param root: must be already loaded
        """
        self.root = root

    @abstractmethod
    async def handle(self, reader, writer):
        """Handle request."""


class WebSocketHandler(RequestHandler):
    """Handle websocket connections."""

    @http_request
    async def handle(self, reader, writer, msg):
        """Handle new websocket connection."""
        if msg.method != "GET":
            await send_http_response(writer, 405)
            log.warning("Invalid method %s", msg.method)
            return
        if "sec-websocket-key" not in msg.headers:
            await send_http_response(writer, 400)
            log.warning("Missing Sec-WebSocket-Key header")
            return
        writer.write(websocket.handshake(msg.headers["sec-websocket-key"]))
        await writer.drain()
        bot = chatbot.Chat(
            str(uuid.uuid4()),
            lambda x: self.send_message(writer, self.root.conf["author"], x),
            self.root,
        )
        bot.greet()
        await writer.drain()
        while True:
            frame = await websocket.read_frame(reader)
            if frame.op_code == "TEXT":
                log.info("Asking: %s", frame.data.decode())
                msg = {}
                txt = frame.data.decode()
                try:
                    msg = json.loads(txt)
                except json.decoder.JSONDecodeError:
                    log.warning("User sent message with invalid json format: %s", txt)
                    self.send_error(writer, f"Invalid JSON format '{txt}'")
                if "text" in msg:
                    bot.ask(chatbot.Message(msg["text"]))
                else:
                    self.send_error(writer, "Missing 'text' key in JSON")
            elif frame.op_code == "CLOSE":
                self.send_close(writer, frame.data)
                break
            elif frame.op_code == "PING":
                self.send_pong(writer, frame.data)
            await writer.drain()

    @staticmethod
    def send_close(writer, text):
        """Send close frame."""
        sendback = 0b1000100000000010
        sendback = sendback.to_bytes(2, "big")
        sendback += text
        writer.write(sendback)

    @staticmethod
    def send_pong(writer, data):
        """Send pong frame."""
        writer.write(websocket.get_frame("PONG", data))

    @staticmethod
    def send_packet(writer, packet):
        """Send packet."""
        packet = json.dumps(packet)
        log.debug("Sending: %s", packet)
        writer.write(websocket.get_frame("TEXT", packet.encode()))

    def send_message(self, writer, author, message):
        """Send back message."""
        packet = {"author": author, "text": message.text}
        self.send_packet(writer, packet)

    def send_error(self, writer, txt):
        """Send error message."""
        self.send_packet(writer, {"error": txt})


class SlackHandler(RequestHandler):
    """Handle slack connections."""

    @http_request
    async def handle(self, reader, writer, msg):
        """Handle new slack connection."""


async def start_runner(conf: dict):
    """Enter main loop."""
    root = chatbot.InterfaceRoot(conf)
    root.load()
    force_bind = conf.get("force_bind", False)
    servers = []
    if conf.get("websocket_port"):
        servers.append(
            await asyncio.start_server(
                WebSocketHandler(root).handle,
                host="localhost",
                port=conf["websocket_port"],
                reuse_port=force_bind,
            )
        )
    if conf.get("slack_port"):
        servers.append(
            await asyncio.start_server(
                SlackHandler(root).handle,
                host="localhost",
                port=conf["slack_port"],
                reuse_port=force_bind,
            )
        )
    await run_servers_stacked(*servers)


def start(conf: dict) -> None:
    """Start server listening on given ports provided by conf.

    We serve forever until interrupted or terminated.
    """
    try:
        asyncio.run(start_runner(conf))
    except KeyboardInterrupt:
        log.info("Server shutdown")
