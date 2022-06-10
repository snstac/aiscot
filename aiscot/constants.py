#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Greg Albrecht <oss@undef.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author:: Greg Albrecht W2GMD <oss@undef.net>
#

"""AISCOT Constants."""

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


DEFAULT_LISTEN_PORT: int = 5050
DEFAULT_LISTEN_HOST: str = "0.0.0.0"

DEFAULT_COT_STALE: str = "3600"  # 1 hour
DEFAULT_COT_TYPE: str = "a-u-S-X-M"

DEFAULT_POLL_INTERVAL: int = 61

DEFAULT_MID_DB_FILE = os.getenv(
    "MID_DB_FILE",
    pkg_resources.resource_filename(
        __name__,
        "data/MaritimeIdentificationDigits-bb62983a-cf0e-40a1-9431-cd54eaeb1c85.csv",
    ),
)
DEFAULT_SHIP_DB_FILE = os.getenv(
    "SHIP_DB_FILE",
    pkg_resources.resource_filename(
        __name__, "data/yadd_mmsi_ship_2021-11-03-170131.txt"
    ),
)
