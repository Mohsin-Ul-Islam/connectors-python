#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""
Command Line Interface.

Parses arguments and call run() with them.
"""
from argparse import ArgumentParser
import os
import logging
import asyncio
import signal
import functools

from envyaml import EnvYAML

from connectors.logger import logger, set_logger
from connectors.source import get_data_sources
from connectors.utils import get_event_loop
from connectors import __version__
from connectors.services.sync import SyncService


def _parser():
    parser = ArgumentParser(prog="elastic-ingest")

    parser.add_argument(
        "--action",
        type=str,
        default="poll",
        choices=["poll", "list"],
        help="What elastic-ingest should do",
    )

    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        help="Configuration file",
        default=os.path.join(os.path.dirname(__file__), "..", "config.yml"),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Run the event loop in debug mode.",
    )

    parser.add_argument(
        "--sync-now",
        action="store_true",
        default=False,
        help="Force a sync on first run for each connector.",
    )

    parser.add_argument(
        "--filebeat",
        action="store_true",
        default=False,
        help="Output in filebeat format.",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Display the version and exit.",
    )

    parser.add_argument(
        "--one-sync",
        action="store_true",
        default=False,
        help="Runs a single sync and exits.",
    )

    parser.add_argument(
        "--uvloop",
        action="store_true",
        default=False,
        help="Use uvloop if possible",
    )

    return parser


def run(args):
    """Runner"""
    # just display the list of connectors
    if args.action == "list":
        logger.info("Registered connectors:")
        config = EnvYAML(args.config_file)
        for source in get_data_sources(config):
            logger.info(f"- {source.__doc__.strip()}")
        logger.info("Bye")
        return 0

    service = SyncService(args)
    coro = service.run()
    loop = get_event_loop(args.uvloop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, functools.partial(service.shutdown, sig))

    try:
        return loop.run_until_complete(coro)
    except asyncio.CancelledError:
        return 0
    finally:
        logger.info("Bye")

    return -1


def main(args=None):
    parser = _parser()
    args = parser.parse_args(args=args)
    if args.version:
        print(__version__)
        return 0
    set_logger(args.debug and logging.DEBUG or logging.INFO, filebeat=args.filebeat)
    return run(args)
