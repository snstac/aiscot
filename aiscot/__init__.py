#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AIS Cursor-On-Target Gateway.

"""
AIS Cursor-On-Target Gateway.
~~~~


:author: Greg Albrecht W2GMD <oss@undef.net>
:copyright: Copyright 2022 Greg Albrecht
:license: Apache License, Version 2.0
:source: <https://github.com/ampledata/aiscot>

"""

from .constants import (  # NOQA
    LOG_FORMAT,
    LOG_LEVEL,
    DEFAULT_AIS_PORT,
    DEFAULT_COT_TYPE,
    DEFAULT_COT_STALE,
    DEFAULT_POLL_INTERVAL,
    MID_DB_FILE,
    SHIP_DB_FILE,
    DEFAULT_COT_URL,
)

from .functions import (  # NOQA
    ais_to_cot,
    read_known_craft,
    get_mid,
    get_aton,
    get_sar,
    get_crs,
    get_shipname,
    ais_to_cot_xml,
)

from .classes import AISWorker  # NOQA

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"
