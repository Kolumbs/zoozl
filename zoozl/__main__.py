"""
Zoozl services hub
"""
import argparse
import logging

from .server import start


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Zoozl hub of services')
    parser.add_argument(
        'port',
        type = int,
        help = 'port number to use for service',
    )
    parser.add_argument(
        '-v',
        action = "store_true",
        help = 'enable verbose debugging mode',
    )
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(level=10)
    else:
        logging.basicConfig(level=20)
    start(args.port)
