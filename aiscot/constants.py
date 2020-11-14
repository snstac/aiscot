#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Constants."""

import logging
import os
import re

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2020 Orion Labs, Inc."
__license__ = "Apache License, Version 2.0"


if bool(os.environ.get('DEBUG')):
    LOG_LEVEL = logging.DEBUG
    LOG_FORMAT = logging.Formatter(
        ('%(asctime)s aiscot %(levelname)s %(name)s.%(funcName)s:%(lineno)d '
         ' - %(message)s'))
    logging.debug('aiscot Debugging Enabled via DEBUG Environment Variable.')
else:
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = logging.Formatter(
        ('%(asctime)s aiscot %(levelname)s - %(message)s'))

DEFAULT_AIS_PORT: int = 5050
DEFAULT_STALE: int = 600
DEFAULT_TYPE: str = "a-n-S-X-M"
