"""Operator CLI: python -m app.cli <command> [--db PATH]."""

import argparse
import importlib

from app import settings
from app.db import connect
from app.jobs.commands import COMMANDS


def main(argv=None):
    for module in settings.JOB_MODULES:
        importlib.import_module(module)
    parser = argparse.ArgumentParser(prog="app.cli")
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--db", default="invoices.db")
    args = parser.parse_args(argv)
    COMMANDS[args.command](connect(args.db))


if __name__ == "__main__":
    main()
