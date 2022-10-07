"""Zoozl services hub"""
# pylint: disable=invalid-name
import argparse
import base64
from dataclasses import dataclass
import hashlib
import http.client
import logging
import socketserver
import sys


log = logging.getLogger("zoozl")

def tcp_line(sock):
    """
    consume first TCP line
    if valid HTTP then return method, request-uri tuple
    """
    block = sock.recv(1)
    if block == b'\r':
        block = sock.recv(1)
        if block == b'\n':
            block = sock.recv(1)
    method = b""
    request_uri = b""
    a = 0
    while block != b'\n':
        if block == b' ':
            a += 1
        if a == 0:
            method += block
        elif a == 1:
            request_uri += block
        block = sock.recv(1)
    return (method, request_uri)

def apply_mask(data, mask):
    """
    Apply masking to the data of a WebSocket message.

    Args:
        data: data to mask.
        mask: 4-bytes mask.

    """
    if len(mask) != 4:
        raise ValueError("mask must contain 4 bytes")
    data_int = int.from_bytes(data, sys.byteorder)
    mask_repeated = mask * (len(data) // 4) + mask[: len(data) % 4]
    mask_int = int.from_bytes(mask_repeated, sys.byteorder)
    return (data_int ^ mask_int).to_bytes(len(data), sys.byteorder)


@dataclass
class Frame:
    """Websocket frame"""
    op_code: str
    text: bytes = b""
    attachment: bytes = b""


class ZoozlBot(socketserver.StreamRequestHandler):
    """TCP server that listens on port for Zoozl boot calls"""

    def handle(self):
        response = tcp_line(self.request) # Need to read request line for headers to read
        if response[0] != b"GET":
            msg = 'Unrecognised message from client: ' + str(self.client_address)
            log.info(msg)
            log.info(response)
            return
        headers = http.client.parse_headers(self.rfile)
        if "Sec-WebSocket-Key" not in headers:
            sendback = b'HTTP/1.1 400 Missing Sec-WebSocket-Key header\r\n'
            self.request.send(sendback)
        self.request.send(self.handshake(headers["Sec-WebSocket-Key"]))
        while True:
            frame = self.read_frame()
            if frame.op_code == "text":
                self.send_text_frame(frame.text)
            elif frame.op_code == "close":
                self.send_close(frame.text)
                break
            elif frame.op_code == "ping":
                self.send_pong()

    def read_frame(self):
        """read one frame"""
        data = self.request.recv(1)
        data = data[0]
        fin = data & 0b10000000
        if not fin:
            log.warning("Frames fragmentation unuspported")
        op_code = data & 0b00001111
        data = self.request.recv(1)[0]
        length = data & 0b01111111
        if not data & 0b10000000:
            mask_bit = 0
            log.warning("NO MASKING GET OUT")
        else:
            mask_bit = 1
        if mask_bit:
            mask = self.request.recv(4)
        if length >= 126:
            log.warning("HANDLE EXTENDED PAYLOAD LENGTH")
        data = self.request.recv(length)
        if mask_bit:
            data = apply_mask(data, mask)
        if op_code == 9:
            new_frame = Frame("ping")
            return new_frame
        if op_code == 1:
            new_frame = Frame("text", data)
            return new_frame
        if op_code == 8:
            new_frame = Frame("close", data)
            return new_frame
        return Frame("unknown")

    def send_close(self, text):
        """send close frame"""
        sendback = 0b1000100000000010
        sendback = sendback.to_bytes(2, "big")
        sendback += text
        self.request.send(sendback)

    def send_pong(self):
        """send pong frame"""
        sendback = 0b1000100100000000
        sendback = sendback.to_bytes(2, "big")
        self.request.send(sendback)

    def send_text_frame(self, text):
        """send text frame"""
        log.warning("received text: %s", text.decode())
        sendback = 0b1000000100000101
        sendback = sendback.to_bytes(2, "big")
        sendback += b"Hello"
        self.request.send(sendback)

    def handshake(self, webkey):
        """Respond with valid websocket handshake"""

        magic_uuid = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        webkey = webkey.encode() + magic_uuid
        hasher = hashlib.sha1()
        hasher.update(webkey)
        key = hasher.digest()
        key = base64.b64encode(key)
        sendback = b"HTTP/1.1 101 Switching Protocols\r\n"
        sendback += b"Upgrade: websocket\r\n"
        sendback += b"Connection: Upgrade\r\n"
        sendback += b"Sec-WebSocket-Accept: " + key + b"\r\n"
        sendback += b"\r\n"
        return sendback


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server running on threads"""


def start(port):
    """starts listening on given port"""
    with ThreadedTCPServer(('', port), ZoozlBot) as server:
        log.info('Server started listening on port: %s', port)
        sys.stdout.flush()
        server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Zoozl hub of services')
    parser.add_argument(
        'port',
        type = int,
        help = 'port number to use for service',
    )
    args = parser.parse_args()
    start(args.port)
