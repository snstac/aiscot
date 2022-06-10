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

"""
AISCOT: AIS Cursor-On-Target Gateway.
~~~~

:author: Greg Albrecht W2GMD <oss@undef.net>
:copyright: Copyright 2022 Greg Albrecht
:license: Apache License, Version 2.0
:source: <https://github.com/ampledata/aiscot>
"""

from .constants import (  # NOQA
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

from .functions import (  # NOQA
    ais_to_cot,
    read_known_craft,
    get_mid,
    get_aton,
    get_sar,
    get_crs,
    get_shipname,
    ais_to_cot_xml,
    create_tasks,
)

from .classes import AISWorker  # NOQA

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"
