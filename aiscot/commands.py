#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Commands."""

import argparse
import asyncio
import concurrent
import os

import pytak

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


async def main(opts):
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    msg_queue: asyncio.Queue = asyncio.Queue(loop=loop)

    aisworker = aiscot.AISWorker(
        msg_queue=msg_queue,
        ais_port=opts.ais_port,
        stale=opts.stale
    )

    cot_host, cot_port = pytak.split_host(opts.cot_host, opts.cot_port)

    client_factory = pytak.AsyncNetworkClient(msg_queue, on_con_lost)
    transport, protocol = await loop.create_connection(
        lambda: client_factory, cot_host, cot_port)

    cotworker = pytak.AsyncCoTWorker(msg_queue, transport)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    tasks: set = set()
    tasks.add(asyncio.ensure_future(msg_queue.join()))
    tasks.add(asyncio.ensure_future(cotworker.run()))
    tasks.add(asyncio.ensure_future(aisworker.run()))
    tasks.add(await on_con_lost)

    done, pending = loop.run_until_complete(
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED))

    for task in done:
        print(f'Task Completed: {task}')


def cli():
    """Command Line interface for AIS Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--ais_port', help='AIS UDP Port',
        default=aiscot.DEFAULT_AIS_PORT
    )
    parser.add_argument(
        '-C', '--cot_host', help='Cursor-on-Target Host or Host:Port',
        required=True
    )
    parser.add_argument(
        '-P', '--cot_port', help='CoT Destination Port'
    )
    parser.add_argument(
        '-B', '--broadcast', help='UDP Broadcast CoT?',
        action='store_true'
    )
    parser.add_argument(
        '-S', '--stale', help='CoT Stale period, in hours',
    )
    opts = parser.parse_args()

    asyncio.run(main(opts), debug=bool(os.environ.get('DEBUG')))


if __name__ == '__main__':
    cli()
