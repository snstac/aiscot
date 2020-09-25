#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AIS Cursor-on-Target Gateway.

"""
AIS Cursor-on-Target Gateway.
~~~~


:author: Greg Albrecht W2GMD <oss@undef.net>
:copyright: Copyright 2020 Orion Labs, Inc.
:license: Apache License, Version 2.0
:source: <https://github.com/ampledata/aiscot>

"""

from .constants import (LOG_FORMAT, LOG_LEVEL, DEFAULT_COT_PORT,  # NOQA
                        DEFAULT_AIS_PORT)

from .functions import ais_to_cot  # NOQA

from .classes import AISCoT  # NOQA

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'
