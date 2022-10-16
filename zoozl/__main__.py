"""
Zoozl services hub
"""
import argparse
import logging

from .zoozl import start


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
