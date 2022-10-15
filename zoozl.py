"""Zoozl services hub"""
import argparse
import http.client
import logging
import socketserver
import sys

import websocket


log = logging.getLogger("zoozl")

# pylint: disable=invalid-name
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


class ZoozlBot(socketserver.StreamRequestHandler):
    """TCP server that listens on port for Zoozl boot calls"""

    def handle(self):
        response = tcp_line(self.request) # Need to read request line for headers to read
        if response[0] != b"GET":
            log.info('Unrecognised message from %s: %s', self.client_address, response)
            return
        log.info("Client Connected: %s", self.client_address)
        headers = http.client.parse_headers(self.rfile)
        if "Sec-WebSocket-Key" not in headers:
            sendback = b'HTTP/1.1 400 Missing Sec-WebSocket-Key header\r\n'
            self.request.send(sendback)
            return
        self.request.send(websocket.handshake(headers["Sec-WebSocket-Key"]))
        while True:
            frame = websocket.read_frame(self.request)
            if frame.op_code == "TEXT":
                self.send_text_frame(frame.data)
            elif frame.op_code == "CLOSE":
                self.send_close(frame.data)
                break
            elif frame.op_code == "PING":
                self.send_pong(frame.data)

    def send_close(self, text):
        """send close frame"""
        sendback = 0b1000100000000010
        sendback = sendback.to_bytes(2, "big")
        sendback += text
        self.request.send(sendback)

    def send_pong(self, data):
        """send pong frame"""
        self.request.send(websocket.get_frame("PONG", data))

    def send_text_frame(self, text):
        """send text frame"""
        log.warning("received text: %s", text.decode())
        sendback = b'{"author": "Oscar", "text": "Hello!"}'
        self.request.send(websocket.get_frame("TEXT", sendback))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server running on threads"""


def start(port):
    """starts listening on given port"""
    with ThreadedTCPServer(('', port), ZoozlBot) as server:
        log.info('Server started listening on port: %s', port)
        sys.stdout.flush()
        server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=20)
    parser = argparse.ArgumentParser(description='Zoozl hub of services')
    parser.add_argument(
        'port',
        type = int,
        help = 'port number to use for service',
    )
    args = parser.parse_args()
    start(args.port)
