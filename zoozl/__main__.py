"""Zoozl services hub."""

import argparse
import logging
import tomllib

from .server import start


def get_conf(path):
    """Return dict object as configuration."""
    conf = {}
    if path:
        with open(path, "rb") as fname:
            conf = tomllib.load(fname)
    if "author" not in conf:
        conf["author"] = "Zoozl"
    return conf


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zoozl hub of services")
    parser.add_argument(
        "port",
        type=int,
        help="port number to use for service",
    )
    parser.add_argument(
        "-v",
        action="store_true",
        help="enable verbose debugging mode",
    )
    parser.add_argument(
        "--conf",
        type=str,
        help="path for configuration",
    )
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(level=10)
    else:
        logging.basicConfig(level=20)
    start(args.port, get_conf(args.conf))
