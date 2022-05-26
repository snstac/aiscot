#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""AIS Cursor-On-Target Constants."""

import logging
import os
import pkg_resources

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


if bool(os.environ.get("DEBUG")):
    LOG_LEVEL = logging.DEBUG
    LOG_FORMAT = logging.Formatter(
        (
            "%(asctime)s aiscot %(levelname)s %(name)s.%(funcName)s:%(lineno)d "
            " - %(message)s"
        )
    )
    logging.debug("aiscot Debugging Enabled via DEBUG Environment Variable.")
else:
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = logging.Formatter(("%(asctime)s aiscot %(levelname)s - %(message)s"))

DEFAULT_AIS_PORT: int = 5050
DEFAULT_COT_STALE: int = 3600  # 1 hour
DEFAULT_COT_TYPE: str = "a-u-S-X-M"
DEFAULT_POLL_INTERVAL: int = 61
DEFAULT_COT_URL: str = "udp://239.2.3.1:6969"  # ATAK Default multicast

MID_DB_FILE = os.getenv(
    "MID_DB_FILE",
    pkg_resources.resource_filename(
        __name__,
        "data/MaritimeIdentificationDigits-bb62983a-cf0e-40a1-9431-cd54eaeb1c85.csv",
    ),
)
SHIP_DB_FILE = os.getenv(
    "SHIP_DB_FILE",
    pkg_resources.resource_filename(
        __name__, "data/yadd_mmsi_ship_2021-11-03-170131.txt"
    ),
)
