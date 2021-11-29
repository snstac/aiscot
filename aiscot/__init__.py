#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AIS Cursor-on-Target Gateway.

"""
AIS Cursor-on-Target Gateway.
~~~~


:author: Greg Albrecht W2GMD <oss@undef.net>
:copyright: Copyright 2021 Greg Albrecht, Inc.
:license: Apache License, Version 2.0
:source: <https://github.com/ampledata/aiscot>

"""

from .constants import (LOG_FORMAT, LOG_LEVEL, DEFAULT_AIS_PORT,  # NOQA
                        DEFAULT_COT_TYPE, DEFAULT_COT_STALE,
                        DEFAULT_POLL_INTERVAL)

from .functions import (ais_to_cot, read_known_craft, get_mid, get_aton, # NOQA
                        get_sar, get_crs, get_shipname, ais_to_cot_xml)

from .classes import AISWorker  # NOQA

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2021 Greg Albrecht, Inc."
__license__ = "Apache License, Version 2.0"
