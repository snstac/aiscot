#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Commands."""

import argparse
import queue
import time

import pytak

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


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

    threads: list = []
    msg_queue: queue.Queue = queue.Queue()

    aisworker = aiscot.AISWorker(
        msg_queue=msg_queue,
        ais_port=opts.ais_port,
        stale=opts.stale
    )
    threads.append(aisworker)

    worker_count = 2
    for wc in range(0, worker_count - 1):
        threads.append(
            pytak.CoTWorker(
                msg_queue=msg_queue,
                cot_host=opts.cot_host,
                cot_port=opts.cot_port,
                broadcast=opts.broadcast
            )
        )

    try:
        [thr.start() for thr in threads]  # NOQA pylint: disable=expression-not-assigned
        msg_queue.join()

        while all([thr.is_alive() for thr in threads]):
            time.sleep(0.01)
    except KeyboardInterrupt:
        [thr.stop() for thr in
         threads]  # NOQA pylint: disable=expression-not-assigned
    finally:
        [thr.stop() for thr in
         threads]  # NOQA pylint: disable=expression-not-assigned


if __name__ == '__main__':
    cli()
