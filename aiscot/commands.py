#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""AIS Cursor-On-Target Gateway Commands."""

import argparse
import asyncio
import configparser
import logging
import os
import sys

from urllib.parse import urlparse, ParseResult

import pytak

import aiscot

# Python 3.6 support:
if sys.version_info[:2] >= (3, 7):
    from asyncio import get_running_loop
else:
    from asyncio import (  # pylint: disable=no-name-in-module
        _get_running_loop as get_running_loop,
    )


__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


async def main(config):
    """Main program function."""
    tx_queue: asyncio.Queue = asyncio.Queue()
    rx_queue: asyncio.Queue = asyncio.Queue()
    cot_url: ParseResult = urlparse(config["aiscot"].get("COT_URL"))

    # Create our CoT Event Queue Worker
    reader, writer = await pytak.protocol_factory(cot_url)
    write_worker = pytak.EventTransmitter(tx_queue, writer)
    read_worker = pytak.EventReceiver(rx_queue, reader)

    message_worker = aiscot.AISWorker(tx_queue, config)

    await tx_queue.put(pytak.hello_event("aiscot"))

    done, _ = await asyncio.wait(
        set([message_worker.run(), read_worker.run(), write_worker.run()]),
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in done:
        print(f"Task completed: {task}")


def cli():
    """Command Line interface for AIS Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--CONFIG_FILE", dest="CONFIG_FILE", default="config.ini", type=str
    )
    namespace = parser.parse_args()
    cli_args = {k: v for k, v in vars(namespace).items() if v is not None}

    # Read config:
    env_vars = os.environ
    env_vars["COT_URL"] = env_vars.get("COT_URL", aiscot.DEFAULT_COT_URL)
    config = configparser.ConfigParser(env_vars)
    
    config_file = cli_args.get("CONFIG_FILE")
    if os.path.exists(config_file):
        logging.info("Reading configuration from %s", config_file)
        config.read(config_file)
    else:
        config.add_section("aiscot")

    if sys.version_info[:2] >= (3, 7):
        asyncio.run(main(config), debug=config["aiscot"].getboolean("DEBUG"))
    else:
        loop = get_running_loop()
        try:
            loop.run_until_complete(main(config))
        finally:
            loop.close()


if __name__ == "__main__":
    cli()
