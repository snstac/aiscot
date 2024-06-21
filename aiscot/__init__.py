#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __init__.py from https://github.com/snstac/aiscot
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

"""AISCOT: Display Ships in TAK - AIS to TAK Gateway"""

__version__ = "6.0.0-beta4"

# Python 3.6 test/build work-around:
try:
    from .constants import (
        LOG_FORMAT,
        LOG_LEVEL,
        DEFAULT_LISTEN_PORT,
        DEFAULT_LISTEN_HOST,
        DEFAULT_COT_TYPE,
        DEFAULT_COT_STALE,
        DEFAULT_POLL_INTERVAL,
        DEFAULT_MID_DB_FILE,
        DEFAULT_SHIP_DB_FILE,
    )

    from .functions import ais_to_cot, create_tasks

    from .ais_functions import get_known_craft

    from .classes import AISWorker
except ImportError:
    import warnings

    warnings.warn("COMPAT: Python 3.6. Ignoring ImportError.")
