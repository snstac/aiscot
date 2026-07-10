#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com/
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

"""AISCOT Ship Classification Tests."""

import zipfile

import pytest

from aiscot import shipclass


@pytest.mark.parametrize(
    "mmsi,shiptype,expected",
    [
        ("366892000", "80", shipclass.SHIPCLASS_TANKER),
        ("366892000", "85", shipclass.SHIPCLASS_TANKER),
        ("366892000", "70", shipclass.SHIPCLASS_CARGO),
        ("366892000", "79", shipclass.SHIPCLASS_CARGO),
        ("366892000", "60", shipclass.SHIPCLASS_PASSENGER),
        ("366892000", "50", shipclass.SHIPCLASS_SPECIAL),
        ("366892000", "52", shipclass.SHIPCLASS_SPECIAL),
        ("366892000", "40", shipclass.SHIPCLASS_HIGHSPEED),
        ("366892000", "30", shipclass.SHIPCLASS_FISHING),
        ("366892000", "36", shipclass.SHIPCLASS_CLASS_B),
        ("366892000", "37", shipclass.SHIPCLASS_CLASS_B),
        # 31 towing / 33 dredging / 35 MilOps are OTHER in AIS-catcher:
        ("366892000", "31", shipclass.SHIPCLASS_UNKNOWN),
        ("366892000", "35", shipclass.SHIPCLASS_UNKNOWN),
        # SeaVision-style single-digit categories:
        ("366892000", "8", shipclass.SHIPCLASS_TANKER),
        ("366892000", "7", shipclass.SHIPCLASS_CARGO),
        ("366892000", "6", shipclass.SHIPCLASS_PASSENGER),
        ("366892000", "4", shipclass.SHIPCLASS_HIGHSPEED),
        ("366892000", "", shipclass.SHIPCLASS_UNKNOWN),
        ("366892000", None, shipclass.SHIPCLASS_UNKNOWN),
        # MMSI rules outrank ship type:
        ("970123456", "80", shipclass.SHIPCLASS_SARTEPIRB),
        ("993692016", "", shipclass.SHIPCLASS_ATON),
        ("3669708", "80", shipclass.SHIPCLASS_STATION),
    ],
)
def test_classify_vessel(mmsi, shiptype, expected):
    assert shipclass.classify_vessel(mmsi, shiptype) == expected


def test_shipclass_argb_signed():
    """CoT <color argb> takes a signed 32-bit int (tanker red = -65536)."""
    assert shipclass.shipclass_argb(shipclass.SHIPCLASS_TANKER) == -65536
    assert shipclass.shipclass_argb("bogus") == shipclass.shipclass_argb(
        shipclass.SHIPCLASS_UNKNOWN
    )


def test_vessel_iconsetpath():
    assert shipclass.vessel_iconsetpath(shipclass.SHIPCLASS_TANKER, True) == (
        f"{shipclass.AIS_SHIPS_ICONSET_UID}/Ships/tanker_underway.png"
    )
    assert shipclass.vessel_iconsetpath(shipclass.SHIPCLASS_CARGO, False) == (
        f"{shipclass.AIS_SHIPS_ICONSET_UID}/Ships/cargo_stopped.png"
    )
    # AtoN / base station / SART have a single (diamond) icon:
    assert shipclass.vessel_iconsetpath(shipclass.SHIPCLASS_ATON, True) == (
        f"{shipclass.AIS_SHIPS_ICONSET_UID}/Ships/aton.png"
    )


def test_get_shiptype():
    assert shipclass.get_shiptype({"shiptype": 52}) == "52"
    assert shipclass.get_shiptype({"TYPE": "70"}) == "70"
    assert shipclass.get_shiptype({"vesselType": "52-Tug"}) == "52"
    # Lowercase "type" is the AIS *message* type, never a ship type:
    assert shipclass.get_shiptype({"type": 3}) == ""
    assert shipclass.get_shiptype({}) == ""


def test_get_underway():
    # SOG present: SOG decides (0.1-knot AIS units; floor is 0.5 knots).
    assert shipclass.get_underway({"speed": 64}) is True
    assert shipclass.get_underway({"speed": 0}) is False
    assert shipclass.get_underway({"speed": 0, "status": 0}) is False
    # Crews leave "Moored" set while sailing — SOG outranks nav status:
    assert shipclass.get_underway({"speed": 64, "status": 5}) is True
    # No SOG: parked nav statuses (1 AtAnchor, 5 Moored, 6 Aground) decide.
    assert shipclass.get_underway({"status": 5}) is False
    assert shipclass.get_underway({"NAVSTAT": 1}) is False
    assert shipclass.get_underway({"status": 0}) is True
    # Neither: unknown.
    assert shipclass.get_underway({}) is None


@pytest.mark.parametrize(
    "name,craft,expected",
    [
        ("DELORES", {"shiptype": 52}, "T/B DELORES"),
        ("SAN FRANCISCO", {"shiptype": 50}, "P/V SAN FRANCISCO"),
        ("EVER GIVEN", {"shiptype": 71}, "M/V EVER GIVEN"),
        ("FRONT TIGER", {"shiptype": 84}, "M/T FRONT TIGER"),
        ("STINSON", {"vesselType": "7"}, "M/V STINSON"),
        # Embedded slashless prefix gets normalized, not stacked:
        ("Pv Golden Gate", {"shiptype": 50}, "P/V Golden Gate"),
        # Already-prefixed names pass verbatim:
        ("M/V EVER GIVEN", {"shiptype": 71}, "M/V EVER GIVEN"),
        ("SAR RESCUE 1", {"shiptype": 51}, "SAR RESCUE 1"),
        # No conventional prefix for this type:
        ("SOME BOAT", {"shiptype": 60}, "SOME BOAT"),
        ("SOME BOAT", {}, "SOME BOAT"),
        ("", {"shiptype": 52}, ""),
    ],
)
def test_prefix_vessel_name(name, craft, expected):
    assert shipclass.prefix_vessel_name(name, craft) == expected


def test_iconset_zip_matches_module():
    """The bundled iconset zip must contain an icon for every class/motion
    combination the module can emit, under the uid-stable layout."""
    from aiscot.constants import DEFAULT_MID_DB_FILE
    from pathlib import Path

    zip_path = (
        Path(DEFAULT_MID_DB_FILE).parent / shipclass.AIS_SHIPS_ICONSET_FILENAME
    )
    assert zip_path.exists(), f"missing {zip_path} - run scripts/build_ais_iconset.py"

    names = set(zipfile.ZipFile(zip_path).namelist())
    assert "iconset.xml" in names
    for sc in shipclass.SHIPCLASS_HEX:
        for underway in (True, False):
            icon = shipclass.vessel_icon_name(sc, underway)
            assert f"{shipclass.AIS_SHIPS_ICONSET_GROUP}/{icon}" in names
