"""SMTP server.

Example usage:
    ```python
    from tests.fixtures import smtp_server

    def setUpModule():
        smtp_server.configure()

    def tearDownModule():
        smtp_server.terminate()
    ```
"""

import subprocess

from tests.fixtures import network


SMTP_SERVER_PROCESS = None
SMTP_SERVER_PORT = 8090


def configure(port: int = SMTP_SERVER_PORT, config_file: str = "tests/data/smtpd.conf"):
    """Configure smtp server."""
    global SMTP_SERVER_PROCESS
    SMTP_SERVER_PROCESS = subprocess.Popen(
        ["smtpd", "-d", "-f", config_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        network.socket_check(port)
    except Exception as e:
        terminate(e)


def terminate(error: str = ""):
    """Terminate smtp server."""
    global SMTP_SERVER_PROCESS
    if SMTP_SERVER_PROCESS is None:
        raise RuntimeError("Server process not started, run `configure` first")
    SMTP_SERVER_PROCESS.terminate()
    try:
        SMTP_SERVER_PROCESS.wait(timeout=6)
    except subprocess.TimeoutExpired:
        SMTP_SERVER_PROCESS.kill()
        SMTP_SERVER_PROCESS.wait()
    stdout = SMTP_SERVER_PROCESS.stdout.read().decode("utf-8")
    SMTP_SERVER_PROCESS.stdout.close()
    SMTP_SERVER_PROCESS = None
    if error:
        msg = str(error) + "\n" + stdout
        raise AssertionError(msg) from None
    else:
        print(stdout)
