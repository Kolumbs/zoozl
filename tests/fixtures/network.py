"""TCP and network utilities."""

import socket
import time


def socket_check(port, timeout=2):
    """Check if socket is open on port for a given timeout in seconds.

    Otherwise raise an exception.
    """
    time_left = timeout
    while time_left > 0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("localhost", port))
            return
        except ConnectionRefusedError:
            time.sleep(0.1)
            time_left -= 0.1
        finally:
            sock.close()
    raise AssertionError(f"Socket on port {port} did not open up within {timeout} secs")
