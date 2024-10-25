"""Zoozl server process configuration.

Usage of this module is to configure and start zoozl server process.

Example in test module to start zoozl server process:

    ```python
    from tests.fixtures import zoozl_server

    def setUpModule():
        zoozl_server.configure()

    def tearDownModule():
        zoozl_server.terminate()
    ```
"""

import socket
import subprocess
import time


from tests import base as bs

# Store server process
ZOOZL_SERVER_PROCESS = None


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


def terminate(error: str = ""):
    """Terminate zoozl server."""
    global ZOOZL_SERVER_PROCESS
    if ZOOZL_SERVER_PROCESS is None:
        raise RuntimeError("Server process not started, run `configure_server` first")
    ZOOZL_SERVER_PROCESS.terminate()
    try:
        ZOOZL_SERVER_PROCESS.wait(timeout=6)
    except subprocess.TimeoutExpired:
        ZOOZL_SERVER_PROCESS.kill()
        ZOOZL_SERVER_PROCESS.wait()
    stdout = ZOOZL_SERVER_PROCESS.stdout.read().decode("utf-8")
    ZOOZL_SERVER_PROCESS.stdout.close()
    ZOOZL_SERVER_PROCESS = None
    if error:
        msg = str(error) + "\n" + stdout
        raise AssertionError(msg) from None
    else:
        print(stdout)


def configure(config_file: str = "tests/data/conf.toml"):
    """Set up server configuration and start server process."""
    global ZOOZL_SERVER_PROCESS
    conf = bs.load_configuration(config_file)
    args = ["env/bin/python", "-m", "zoozl", "--force-bind"]
    args.append("--conf")
    args.append(config_file)
    ZOOZL_SERVER_PROCESS = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    try:
        if conf["websocket_port"]:
            socket_check(conf["websocket_port"])
    except Exception as e:
        terminate(e)
