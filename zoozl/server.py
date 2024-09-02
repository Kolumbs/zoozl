"""Zoozl server."""

import http.client
import json
import logging
import socketserver
import sys

from zoozl import websocket, chatbot


log = logging.getLogger(__name__)


# pylint: disable=invalid-name
def tcp_line(sock):
    """Consume first TCP line if valid HTTP then return method, request-uri tuple."""
    block = sock.recv(1)
    if block == b"\r":
        block = sock.recv(1)
        if block == b"\n":
            block = sock.recv(1)
    method = b""
    request_uri = b""
    a = 0
    counter = 100
    while block != b"\n" and counter:
        if block == b" ":
            a += 1
        if a == 0:
            method += block
        elif a == 1:
            request_uri += block
        block = sock.recv(1)
        counter -= 1
    return (method, request_uri)


class ZoozlBot(socketserver.StreamRequestHandler):
    """TCP server that listens on port for Zoozl bot calls."""

    def handle(self):
        """Handle any request from external source."""
        if not self.server.root.loaded:
            self.server.root.load()
        try:
            response = tcp_line(
                self.request
            )  # Need to read request line for headers to read
            if response[0] != b"GET":
                log.info(
                    "Unrecognised message from %s: %s", self.client_address, response
                )
                return
            log.info("Client Connected: %s", self.client_address)
            headers = http.client.parse_headers(self.rfile)
            if "Sec-WebSocket-Key" not in headers:
                sendback = b"HTTP/1.1 400 Missing Sec-WebSocket-Key header\r\n"
                self.request.send(sendback)
                return
            self.request.send(websocket.handshake(headers["Sec-WebSocket-Key"]))
            bot = chatbot.Chat(
                self.client_address,
                self.send_message,
                self.server.root,
            )
            bot.greet()
            while True:
                frame = websocket.read_frame(self.request)
                if frame.op_code == "TEXT":
                    log.debug("Asking: %s", frame.data.decode())
                    msg = {}
                    try:
                        msg = json.loads(frame.data.decode())
                    except json.decoder.JSONDecodeError:
                        log.info("Invalid json format: %s", frame.data.decode())
                    if "text" in msg:
                        bot.ask(chatbot.Message(msg["text"]))
                elif frame.op_code == "CLOSE":
                    self.send_close(frame.data)
                    break
                elif frame.op_code == "PING":
                    self.send_pong(frame.data)
        except ConnectionResetError:
            log.info("Client %s dropped connection", self.client_address)

    def send_close(self, text):
        """Send close frame."""
        sendback = 0b1000100000000010
        sendback = sendback.to_bytes(2, "big")
        sendback += text
        self.request.send(sendback)

    def send_pong(self, data):
        """Send pong frame."""
        self.request.send(websocket.get_frame("PONG", data))

    def send_message(self, message):
        """Send back message."""
        packet = {"author": self.server.root.conf["author"], "text": message.text}
        packet = json.dumps(packet)
        log.debug("Sending: %s", packet)
        self.request.send(websocket.get_frame("TEXT", packet.encode()))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server running on threads."""

    def __init__(self, address, mixer, conf):
        """Initialise root object of the chatbot."""
        self.root = chatbot.InterfaceRoot(conf)
        socketserver.TCPServer.__init__(self, address, mixer)


def start(port, conf):
    """Start listening on given port."""
    with ThreadedTCPServer(("", port), ZoozlBot, conf) as server:
        log.info("Server started listening on port: %s", port)
        sys.stdout.flush()
        server.serve_forever()
