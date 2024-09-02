"""Module that allows to interact with websocket frames.

Note on implementation:
    -> Fragmentation not supported
    -> Reading frames with payload more than 125 bytes not supported
"""

import base64
from dataclasses import dataclass
import enum
import hashlib
import sys


FIN = "8"  # Starting nibble of frame in hex string


def apply_mask(data, mask):
    """Apply masking to the data of a WebSocket message.

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
    """Websocket data frame."""

    op_code: str
    data: bytes = b""


class OpCodes(enum.Enum):
    """Op codes into hex nibbles."""

    TEXT = "1"
    BINARY = "2"
    CLOSE = "8"
    PING = "9"
    PONG = "A"


def get_frame(op_code, payload):
    """Encode binary payload as per op_code into correct frame."""
    code = OpCodes[op_code].value
    frame = bytearray.fromhex(f"{FIN}{code}")
    length = len(payload)
    if length > 125:
        raise RuntimeError("unsupported length")
    frame += length.to_bytes(1, byteorder="big")
    frame += payload
    return frame


def read_frame(socket):
    """Read one frame from socket."""
    data = socket.recv(1)
    if len(data) == 0:
        # Here should better response something like close without notice
        return Frame("CLOSE", b"\x03\xe8")
    data = data[0]
    fin = data & 0b10000000
    if not fin:
        raise RuntimeError("Frames fragmentation unsupported")
    op_code = data & 0b00001111
    data = socket.recv(1)[0]
    length = data & 0b01111111
    if not data & 0b10000000:
        raise RuntimeError("Client must send frames masked")
    mask = socket.recv(4)
    if length >= 126:
        raise RuntimeError("Extended payload unsupported")
    data = socket.recv(length)
    data = apply_mask(data, mask)
    if op_code == 9:
        new_frame = Frame("PING", data)
        return new_frame
    if op_code == 1:
        new_frame = Frame("TEXT", data)
        return new_frame
    if op_code == 8:
        # note on upacking status code
        # code = struct.unpack("!H", data[:2])
        new_frame = Frame("CLOSE", data)
        return new_frame
    raise RuntimeError(f"Unsupported frame op code: {op_code}")


def handshake(webkey):
    """Give bytes object for valid websocket handshake."""
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
