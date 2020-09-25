#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Commands."""

import argparse
import time

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def cli():
    """Command Line interface for AIS Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-P', '--ais_port', help='AIS UDP Port',
        default=aiscot.DEFAULT_AIS_PORT
    )
    parser.add_argument(
        '-C', '--cot_host', help='Cursor-on-Target Host or Host:Port',
        required=True
    )
    opts = parser.parse_args()

    aiscot_i = aiscot.AISCoT(opts.ais_port, opts.cot_host)

    try:
        aiscot_i.start()

        while aiscot_i.is_alive():
            time.sleep(0.01)
    except KeyboardInterrupt:
        aiscot_i.stop()
    finally:
        aiscot_i.stop()


if __name__ == '__main__':
    cli()
