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

"""AISCOT Function Tests."""

import io
import xml.etree.ElementTree as ET

import pytest

import aiscot


@pytest.fixture
def sample_data_libais():
    return {
        "id": 1,
        "repeat_indicator": 0,
        "mmsi": 211433000,
        "nav_status": 0,
        "rot_over_range": True,
        "rot": -731.386474609375,
        "sog": 1.100000023841858,
        "position_accuracy": 1,
        "x": -122.65529333333333,
        "y": 37.72890666666667,
        "cog": 80.30000305175781,
        "true_heading": 511,
        "timestamp": 25,
        "special_manoeuvre": 0,
        "spare": 0,
        "raim": True,
        "sync_state": 0,
        "slot_timeout": 3,
        "received_stations": 133,
        "nmea": "!AIVDM,1,1,,B,139`n:0P0;o>Qm@EUc838wvj2<25,0*4E\n",
    }


@pytest.fixture
def sample_data_pyAISm():
    """
    Provides a sample of pyAISm decoded AIS data.
    :returns dict
    """
    return {
        "type": 3,
        "repeat": 0,
        "mmsi": 366892000,
        "status": 0,
        "turn": 0,
        "speed": 64,
        "accuracy": "1",
        "lon": -122.51208,
        "lat": 37.81691333333333,
        "course": 97.10000000000001,
        "heading": 95,
        "second": 9,
        "maneuver": 0,
        "raim": "0",
        "radio": 11729,
    }


@pytest.fixture
def sample_aton():
    """
    Provides a sample of pyAISm decoded AIS data.
    :returns dict
    """
    return {
        "type": 21,
        "repeat": 0,
        "mmsi": 993692016,
        "aid_type": 1,
        "name": "6W",
        "accuracy": "0",
        "lon": -122.804465,
        "lat": 37.70583666666667,
        "to_bow": 0,
        "to_stern": 0,
        "to_port": 0,
        "to_starboard": 0,
        "epfd": 7,
        "second": 61,
        "off_position": "0",
        "regional": 0,
        "raim": "0",
        "virtual_aid": "1",
        "assigned": "0",
        "name_ext": "",
    }


@pytest.fixture
def sample_known_craft():
    sample_csv = """MMSI,NAME,COT,STALE
366892000,TACO_01,a-f-S-T-A-C-O,
"""
    csv_fd = io.StringIO(sample_csv)
    return aiscot.ais_functions.read_known_craft_fd(csv_fd)


def test_ais_to_cot(sample_data_pyAISm):
    cot = aiscot.ais_to_cot(sample_data_pyAISm)
    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-S-X-M"
    assert cot.attrib["uid"] == "MMSI-366892000"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.8169"
    assert point[0].attrib["lon"] == "-122.5121"
    assert point[0].attrib["hae"] == "0.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "95"
    assert track[0].attrib["speed"] == "3.292181069958848"


def test_ais_to_cot_with_known_craft(sample_data_pyAISm, sample_known_craft):
    known_craft_key = "MMSI"
    filter_key = str(sample_data_pyAISm["mmsi"])

    known_craft = (
        list(
            filter(
                lambda x: x[known_craft_key].strip().upper() == filter_key,
                sample_known_craft,
            )
        )
        or [{}]
    )[0]

    cot = aiscot.ais_to_cot(sample_data_pyAISm, known_craft=known_craft)

    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-S-T-A-C-O"
    assert cot.attrib["uid"] == "MMSI-366892000"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.8169"
    assert point[0].attrib["lon"] == "-122.5121"
    assert point[0].attrib["hae"] == "0.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    contact = detail[0].findall("contact")
    assert contact[0].tag == "contact"
    assert contact[0].attrib["callsign"] == "TACO_01"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "95"
    assert track[0].attrib["speed"] == "3.29216"


def test_ais_to_cot_none():
    """Test that `aiscot.ais_to_cot()` only renders valid input data."""
    assert (
        aiscot.ais_to_cot(
            {
                "mmsi": 366892000,
                "lon": 0,
                "lat": 37.81691333333333,
            }
        )
        is None
    )
    assert (
        aiscot.ais_to_cot(
            {
                "mmsi": 366892000,
                "lon": -122.51208,
                "lat": 0,
            }
        )
        is None
    )
    assert (
        aiscot.ais_to_cot(
            {
                "mmsi": "",
                "lon": -122.51208,
                "lat": 37.81691333333333,
            }
        )
        is None
    )
    assert aiscot.ais_to_cot({}) is None


def test_ais_to_cot_dont_ignore_aton(sample_aton):
    """Test ignoring Aids to Naviation (ATON)."""
    assert aiscot.ais_to_cot(sample_aton, {"IGNORE_ATON": False}) is not None


def test_ais_to_cot_ignore_aton(sample_aton):
    """Test ignoring Aids to Naviation (ATON)."""
    assert aiscot.ais_to_cot(sample_aton, {"IGNORE_ATON": True}) is None


def test_ais_to_cot_shipname(sample_data_pyAISm):
    """Test converting AIS to CoT with a known shipname."""
    sample_data_pyAISm["mmsi"] = "303990000"
    cot = aiscot.ais_to_cot(sample_data_pyAISm)

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    contact = detail[0].findall("contact")
    assert contact[0].attrib["callsign"] == "USCG EAGLE"


def test_ais_to_cot_sar(sample_data_pyAISm):
    """Test converting AIS to CoT for a SAR vessel."""
    sample_data_pyAISm["mmsi"] = "303862000"
    cot = aiscot.ais_to_cot(sample_data_pyAISm)

    assert cot.tag == "event"
    assert cot.attrib["type"] == "a-f-S-X-L"


def test_ais_to_cot_crs(sample_data_pyAISm):
    """Test converting AIS to CoT for a CRS vessel."""
    sample_data_pyAISm["mmsi"] = "3669123"
    cot = aiscot.ais_to_cot(sample_data_pyAISm)

    assert cot.tag == "event"
    assert cot.attrib["type"] == "a-f-G-I-U-T"


def test_ais_to_cot(sample_data_pyAISm):
    """Test converting AIS to CoT."""
    cot: bytes = aiscot.cot_to_xml(sample_data_pyAISm)
    assert b"a-f-S-X-M" in cot
    assert b"MMSI-366892000" in cot


@pytest.fixture
def sample_tug(sample_data_pyAISm):
    """A tug with static & voyage data (name + ship type) merged in."""
    craft = dict(sample_data_pyAISm)
    craft["name"] = "DELORES"
    craft["shiptype"] = 52
    return craft


def test_ais_to_cot_vessel_name_prefix(sample_tug):
    """Ship-type name prefix is prepended to the callsign by default."""
    cot = aiscot.ais_to_cot(sample_tug)
    contact = cot.findall("detail")[0].findall("contact")
    assert contact[0].attrib["callsign"] == "T/B DELORES"


def test_ais_to_cot_vessel_name_prefix_disabled(sample_tug):
    cot = aiscot.ais_to_cot(sample_tug, {"VESSEL_NAME_PREFIX": False})
    contact = cot.findall("detail")[0].findall("contact")
    assert contact[0].attrib["callsign"] == "DELORES"


def test_ais_to_cot_shipclass_color(sample_data_pyAISm):
    """Ship-class <color argb> is emitted by default (tanker = red)."""
    sample_data_pyAISm["shiptype"] = 80
    cot = aiscot.ais_to_cot(sample_data_pyAISm)
    color = cot.findall("detail")[0].findall("color")
    assert color[0].attrib["argb"] == "-65536"


def test_ais_to_cot_shipclass_color_disabled(sample_data_pyAISm):
    cot = aiscot.ais_to_cot(sample_data_pyAISm, {"SHIPCLASS_COLORS": False})
    assert not cot.findall("detail")[0].findall("color")


def test_ais_to_cot_shipclass_icons(sample_data_pyAISm):
    """SHIPCLASS_ICONS adds a usericon from the bundled iconset (opt-in)."""
    sample_data_pyAISm["shiptype"] = 80
    cot = aiscot.ais_to_cot(sample_data_pyAISm, {"SHIPCLASS_ICONS": True})
    usericon = cot.findall("detail")[0].findall("usericon")
    assert usericon[0].attrib["iconsetpath"] == (
        f"{aiscot.shipclass.AIS_SHIPS_ICONSET_UID}/Ships/tanker_underway.png"
    )


def test_ais_to_cot_shipclass_icons_default_off(sample_data_pyAISm):
    cot = aiscot.ais_to_cot(sample_data_pyAISm)
    assert not cot.findall("detail")[0].findall("usericon")


def test_ais_to_cot_cot_icon_beats_shipclass_icon(sample_data_pyAISm):
    """An explicit COT_ICON outranks the ship-class icon."""
    config = {"SHIPCLASS_ICONS": True, "COT_ICON": "some-uid/Group/icon.png"}
    cot = aiscot.ais_to_cot(sample_data_pyAISm, config)
    usericon = cot.findall("detail")[0].findall("usericon")
    assert usericon[0].attrib["iconsetpath"] == "some-uid/Group/icon.png"


def test_ais_to_cot_underway_only(sample_data_pyAISm):
    """UNDERWAY_ONLY drops parked hulls; underway traffic still flows."""
    # Underway (speed 64 = 6.4 knots): passes.
    assert aiscot.ais_to_cot(sample_data_pyAISm, {"UNDERWAY_ONLY": True}) is not None
    # SOG zero: suppressed.
    parked = dict(sample_data_pyAISm)
    parked["speed"] = 0
    assert aiscot.ais_to_cot(parked, {"UNDERWAY_ONLY": True}) is None
    # No SOG, Moored: suppressed.
    moored = dict(sample_data_pyAISm)
    del moored["speed"]
    moored["status"] = 5
    assert aiscot.ais_to_cot(moored, {"UNDERWAY_ONLY": True}) is None
    # Default: everything passes.
    assert aiscot.ais_to_cot(parked) is not None


def test_ais_to_cot_underway_only_keeps_aton(sample_aton):
    """AtoN are never underway; UNDERWAY_ONLY must not drop them."""
    assert aiscot.ais_to_cot(sample_aton, {"UNDERWAY_ONLY": True}) is not None
