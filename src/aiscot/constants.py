#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# constants.py from https://github.com/snstac/aiscot
#
# Copyright Sensors & Signals LLC https://www.snstac.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""AISCOT Constants."""

import os

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files

default_mid_file = (
    "data/MaritimeIdentificationDigits-bb62983a-cf0e-40a1-9431-cd54eaeb1c85.csv"
)
default_ship_file = "data/yadd_mmsi_ship_2023-02-11-001541.txt"

_mid = os.environ.get("AISCOT_MID_DB_FILE", default_mid_file)
_ship = os.environ.get("AISCOT_SHIP_DB_FILE", default_ship_file)

DEFAULT_MID_DB_FILE = str(files("aiscot").joinpath(_mid))
DEFAULT_SHIP_DB_FILE = str(files("aiscot").joinpath(_ship))

DEFAULT_LISTEN_PORT: int = 5050
DEFAULT_LISTEN_HOST: str = "0.0.0.0"

DEFAULT_COT_STALE: str = "3600"  # 1 hour
DEFAULT_COT_TYPE: str = "a-u-S-X-M"

DEFAULT_POLL_INTERVAL: int = 61
