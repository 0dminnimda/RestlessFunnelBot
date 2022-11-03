"""
Main command-line interface for the application
"""

import argparse

from RestlessFunnelBot import BOT_NAME, __description__, run

parser = argparse.ArgumentParser(prog=BOT_NAME, description=__description__)

args = parser.parse_args()


if __name__ == "__main__":
    run()
