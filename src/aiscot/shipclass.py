#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# shipclass.py from https://github.com/snstac/aiscot
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

"""AIS-catcher style ship classification, colors & vessel name prefixes.

AIS-catcher (https://github.com/jvde-github/AIS-catcher) collapses AIS ship
type + MMSI into a small ship-class enum and colors every marker by class —
a de-facto standard maritime palette (tankers red, cargo spring green,
passenger blue, ...). This module re-implements the mapping tables and hex
colors from its published behavior (``Source/Tracking/Ships.cpp`` +
``frontend/src/script.js``); the matching marker shapes are redrawn from
scratch in ``scripts/build_ais_iconset.py``, so nothing GPL-licensed is
copied.

One deliberate deviation: AIS-catcher buckets vessels with no mapped ship
type by transponder class (Class B → magenta), which not all AIS feeds
expose. Ship types 36 Sailing / 37 Pleasure are overwhelmingly Class B
transponders, so they stand in for that bucket here.
"""

import re

from typing import Optional

# Ship classes (AIS-catcher ShippingClass, minus PLANE/HELICOPTER — SAR
# aircraft already get a dedicated CoT type via ``get_sar()``).
SHIPCLASS_CARGO = "cargo"
SHIPCLASS_CLASS_B = "classb"
SHIPCLASS_PASSENGER = "passenger"
SHIPCLASS_SPECIAL = "special"
SHIPCLASS_TANKER = "tanker"
SHIPCLASS_HIGHSPEED = "highspeed"
SHIPCLASS_FISHING = "fishing"
SHIPCLASS_UNKNOWN = "unknown"
SHIPCLASS_ATON = "aton"
SHIPCLASS_STATION = "station"
SHIPCLASS_SARTEPIRB = "sartepirb"

# AIS-catcher track/sprite palette (getDefaultTrackColors + sprite pixels).
SHIPCLASS_HEX = {
    SHIPCLASS_CARGO: "#00FF7F",  # spring green
    SHIPCLASS_CLASS_B: "#FF00FF",  # magenta
    SHIPCLASS_PASSENGER: "#0000FF",  # blue
    SHIPCLASS_SPECIAL: "#A52A2A",  # brown (pilot/SAR/tug/law/... 50-59)
    SHIPCLASS_TANKER: "#FF0000",  # red
    SHIPCLASS_HIGHSPEED: "#FFFF00",  # yellow
    SHIPCLASS_FISHING: "#FF1493",  # deep pink
    SHIPCLASS_UNKNOWN: "#12A5ED",  # light azure (also OTHER)
    SHIPCLASS_ATON: "#FFFF00",  # sprite diamond yellow
    SHIPCLASS_STATION: "#0000FF",
    SHIPCLASS_SARTEPIRB: "#FF0000",
}

# Classes drawn as a single motion-independent diamond icon (also used by
# scripts/build_ais_iconset.py when generating the zip).
DIAMOND_SHIPCLASSES = (SHIPCLASS_ATON, SHIPCLASS_STATION, SHIPCLASS_SARTEPIRB)

# Stable uid for the generated ATAK iconset (scripts/build_ais_iconset.py);
# CoT ``iconsetpath`` values referencing the set must never drift from it.
AIS_SHIPS_ICONSET_UID = "3c73f1d2-9a41-4c26-8b6f-51e072d84c1b"
AIS_SHIPS_ICONSET_GROUP = "Ships"
AIS_SHIPS_ICONSET_FILENAME = "ais-ships-iconset.zip"

# Conventional vessel-name prefix by AIS ship type ("T/B Delores"), major
# types only. Some API feeds (e.g. SeaVision) collapse cargo/tanker to the
# single-digit category ("7", "8"); raw AIS feeds ship the full 70-79/80-89
# code, handled by fallback in ``get_vessel_name_prefix()``.
VESSEL_NAME_TYPE_PREFIX = {
    "7": "M/V",  # cargo
    "8": "M/T",  # tanker
    "30": "F/V",  # fishing
    "31": "T/B",  # towing
    "32": "T/B",
    "36": "S/V",  # sailing
    "50": "P/V",  # pilot
    "51": "SAR",
    "52": "T/B",  # tug
    "54": "A/P",  # anti-pollution
    "55": "L/E",  # law enforcement
}

# A name that already leads with a type prefix ("M/V ...", "SAR ...") passes
# verbatim.
VESSEL_NAME_PREFIXED_RE = re.compile(
    r"^(?:[A-Za-z]{1,3}/[A-Za-z]{1,2}|SAR)\s", re.IGNORECASE
)

# AIS nav statuses that mean the hull is parked: 1 AtAnchor, 5 Moored,
# 6 Aground.
PARKED_NAV_STATUS_CODES = {"1", "5", "6"}

KNOTS_TO_MS = 0.514444

# SOG floor for "underway", in m/s (0.5 knots).
UNDERWAY_MIN_SOG_MS = 0.5 * KNOTS_TO_MS

# AIS "SOG not available" sentinel, in knots: raw field 1023 (= 102.3 with
# the 0.1-knot scale); 102.2 and below are real speeds.
SOG_NOT_AVAILABLE_KNOTS = 102.3

# Keys AIS feeds use for ship type. Deliberately excludes lowercase "type",
# which is the AIS *message* type in NMEA-decoded (pyAISm) data.
_SHIPTYPE_KEYS = (
    "shiptype",  # pyAISm Type 5 Static & Voyage data
    "ship_type",
    "SHIPTYPE",
    "TYPE",  # AISHub API
    "vesselType",
    "veselType",  # SeaVision API
    "cargo",
)

_NAV_STATUS_KEYS = ("status", "nav_status", "NAVSTAT", "navStatus")

# SOG keys with the per-feed scale that converts their value to knots:
# pyAISm passes the raw AIS field through (0.1-knot units), while the
# AISHub (format=1) and SeaVision APIs report plain knots.
_SOG_KEY_KNOTS_SCALE = (
    ("speed", 0.1),  # pyAISm raw AIS units
    ("SPEED", 1.0),  # AISHub / SeaVision
    ("SOG", 1.0),  # AISHub format=1 / SeaVision
)


def get_shiptype(craft: dict) -> str:
    """Extract the AIS ship type code from decoded AIS data.

    Handles ``52`` ints, ``"52"`` strings and ``"52-Tug"`` style values.
    """
    for key in _SHIPTYPE_KEYS:
        value = craft.get(key)
        if value in (None, ""):
            continue
        code = str(value).strip().split("-", 1)[0].strip()
        if code:
            return code
    return ""


def get_nav_status(craft: dict) -> str:
    """Extract the AIS navigation status code from decoded AIS data."""
    for key in _NAV_STATUS_KEYS:
        value = craft.get(key)
        if value in (None, ""):
            continue
        return str(value).strip().split("-", 1)[0].strip()
    return ""


def get_sog_ms(craft: dict) -> Optional[float]:
    """Speed over ground in m/s, scaling each feed's key to knots first
    (pyAISm ``speed`` is raw 0.1-knot units; API ``SPEED``/``SOG`` are
    knots). Returns None when SOG is missing or carries the AIS "not
    available" sentinel (raw 1023 / 102.3 knots)."""
    for key, scale in _SOG_KEY_KNOTS_SCALE:
        value = craft.get(key)
        if value in (None, ""):
            continue
        try:
            knots = float(value) * scale
        except (TypeError, ValueError):
            continue
        if knots >= SOG_NOT_AVAILABLE_KNOTS:
            return None
        return knots * KNOTS_TO_MS
    return None


def get_underway(craft: dict) -> Optional[bool]:
    """Is this vessel underway? SOG outranks nav status — crews leave
    "Underway" set at the dock and "Moored" set while sailing. Returns None
    when the data carries neither SOG nor nav status."""
    sog_ms = get_sog_ms(craft)
    if sog_ms is not None:
        return sog_ms >= UNDERWAY_MIN_SOG_MS
    nav_status = get_nav_status(craft)
    if nav_status:
        return nav_status not in PARKED_NAV_STATUS_CODES
    return None


def classify_vessel(mmsi: Optional[str], shiptype: Optional[str]) -> str:
    """Collapse MMSI + AIS ship type into an AIS-catcher ship class.

    MMSI rules first (SART/AtoN/base station), then ship-type ranges — same
    precedence as AIS-catcher ``Ship::getShipTypeClass``.
    """
    _mmsi = str(mmsi or "").strip()
    if _mmsi.isdigit():
        num = int(_mmsi)
        if 970000000 <= num <= 980000000:
            return SHIPCLASS_SARTEPIRB
        if 990000000 <= num <= 999999999:
            return SHIPCLASS_ATON
        if 0 < num < 9000000:
            return SHIPCLASS_STATION
    code = str(shiptype or "").strip()
    if not code.isdigit():
        return SHIPCLASS_UNKNOWN
    stype = int(code)
    if 80 <= stype < 90:
        return SHIPCLASS_TANKER
    if 70 <= stype < 80:
        return SHIPCLASS_CARGO
    if 60 <= stype < 70:
        return SHIPCLASS_PASSENGER
    if 50 <= stype < 60:
        return SHIPCLASS_SPECIAL
    if 40 <= stype < 50:
        return SHIPCLASS_HIGHSPEED
    if stype == 30:
        return SHIPCLASS_FISHING
    if stype in (36, 37):  # sailing/pleasure — Class B stand-in (module doc)
        return SHIPCLASS_CLASS_B
    # SeaVision collapses cargo/tanker/passenger/HSC to single-digit
    # categories.
    if len(code) == 1:
        if stype == 8:
            return SHIPCLASS_TANKER
        if stype == 7:
            return SHIPCLASS_CARGO
        if stype == 6:
            return SHIPCLASS_PASSENGER
        if stype == 4:
            return SHIPCLASS_HIGHSPEED
    return SHIPCLASS_UNKNOWN


def shipclass_hex(shipclass: str) -> str:
    """Marker color for a ship class as a #RRGGBB hex string."""
    return SHIPCLASS_HEX.get(shipclass, SHIPCLASS_HEX[SHIPCLASS_UNKNOWN])


def _hex_to_signed_argb(hex_color: str) -> int:
    val = 0xFF000000 | int(hex_color.lstrip("#"), 16)
    return val - 0x100000000 if val >= 0x80000000 else val


# Precomputed opaque signed-int colors (hot path: one lookup per message).
SHIPCLASS_ARGB = {sc: _hex_to_signed_argb(hx) for sc, hx in SHIPCLASS_HEX.items()}


def shipclass_argb(shipclass: str) -> int:
    """Opaque marker color as the signed 32-bit int CoT ``<color argb>``
    takes."""
    return SHIPCLASS_ARGB.get(shipclass, SHIPCLASS_ARGB[SHIPCLASS_UNKNOWN])


def vessel_icon_name(shipclass: str, underway: bool) -> str:
    """PNG name inside the generated iconset for a class/motion state."""
    if shipclass in DIAMOND_SHIPCLASSES:
        return f"{shipclass}.png"
    return f"{shipclass}_{'underway' if underway else 'stopped'}.png"


def vessel_iconsetpath(shipclass: str, underway: bool) -> str:
    """CoT ``<usericon iconsetpath>`` for a ship class in the generated
    ``ais-ships-iconset.zip`` (dart when underway, circle when stopped)."""
    icon_name = vessel_icon_name(shipclass, underway)
    return f"{AIS_SHIPS_ICONSET_UID}/{AIS_SHIPS_ICONSET_GROUP}/{icon_name}"


def get_vessel_name_prefix(craft: dict) -> Optional[str]:
    """Conventional name prefix ("T/B", "P/V", ...) for this vessel's ship
    type, or None when the type has no conventional prefix."""
    code = get_shiptype(craft)
    prefix = VESSEL_NAME_TYPE_PREFIX.get(code)
    if prefix is None and len(code) == 2 and code[0] in ("7", "8"):
        prefix = VESSEL_NAME_TYPE_PREFIX.get(code[0])
    return prefix


def prefix_vessel_name(name: str, craft: dict) -> str:
    """Prepend the conventional ship-type prefix to a vessel name.

    "SS-style" prefixes are how mariners name traffic: "T/B Delores",
    "P/V Golden Gate". Names that already lead with a prefix pass verbatim;
    names embedding the slashless prefix ("PV GOLDEN GATE") get that token
    normalized instead of stacking another.
    """
    name = (name or "").strip()
    if not name:
        return name
    prefix = get_vessel_name_prefix(craft)
    if not prefix or VESSEL_NAME_PREFIXED_RE.match(name):
        return name
    bare = prefix.replace("/", "")
    if name[: len(bare) + 1].upper() == f"{bare.upper()} ":
        name = name[len(bare) + 1:].strip()
    return f"{prefix} {name}"
