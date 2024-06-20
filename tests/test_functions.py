#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Greg Albrecht <oss@undef.net>
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

from aiscot.ais_functions import read_known_craft_fd
from aiscot.constants import DEFAULT_MID_DB_FILE, DEFAULT_SHIP_DB_FILE
from aiscot.functions import ais_to_cot, ais_to_cot_xml


__author__ = "Greg Albrecht <oss@undef.net>"
__copyright__ = "Copyright 2023 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


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
    return read_known_craft_fd(csv_fd)


def test_ais_to_cot_xml(sample_data_pyAISm):
    cot = ais_to_cot_xml(sample_data_pyAISm)
    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-S-X-M"
    assert cot.attrib["uid"] == "MMSI-366892000"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.81691333333333"
    assert point[0].attrib["lon"] == "-122.51208"
    assert point[0].attrib["hae"] == "9999999.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "95"
    assert track[0].attrib["speed"] == "3.292181069958848"


def test_ais_to_cot_xml_with_known_craft(sample_data_pyAISm, sample_known_craft):
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

    cot = ais_to_cot_xml(sample_data_pyAISm, known_craft=known_craft)

    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-S-T-A-C-O"
    assert cot.attrib["uid"] == "MMSI-366892000"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.81691333333333"
    assert point[0].attrib["lon"] == "-122.51208"
    assert point[0].attrib["hae"] == "9999999.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    contact = detail[0].findall("contact")
    assert contact[0].tag == "contact"
    assert contact[0].attrib["callsign"] == "TACO_01"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "95"
    assert track[0].attrib["speed"] == "3.292181069958848"


def test_ais_to_cot_xml_none():
    """Test that `ais_to_cot_xml()` only renders valid input data."""
    assert (
        ais_to_cot_xml(
            {
                "mmsi": 366892000,
                "lon": 0,
                "lat": 37.81691333333333,
            }
        )
        is None
    )
    assert (
        ais_to_cot_xml(
            {
                "mmsi": 366892000,
                "lon": -122.51208,
                "lat": 0,
            }
        )
        is None
    )
    assert (
        ais_to_cot_xml(
            {
                "mmsi": "",
                "lon": -122.51208,
                "lat": 37.81691333333333,
            }
        )
        is None
    )
    assert ais_to_cot_xml({}) is None


def test_ais_to_cot_xml_dont_ignore_aton(sample_aton):
    """Test ignoring Aids to Naviation (ATON)."""
    assert ais_to_cot_xml(sample_aton, {"IGNORE_ATON": False}) is not None


def test_ais_to_cot_xml_ignore_aton(sample_aton):
    """Test ignoring Aids to Naviation (ATON)."""
    assert ais_to_cot_xml(sample_aton, {"IGNORE_ATON": True}) is None


def test_ais_to_cot_xml_shipname(sample_data_pyAISm):
    """Test converting AIS to CoT with a known shipname."""
    sample_data_pyAISm["mmsi"] = "303990000"
    cot = ais_to_cot_xml(sample_data_pyAISm)

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    contact = detail[0].findall("contact")
    assert contact[0].attrib["callsign"] == "USCG EAGLE"


def test_ais_to_cot_xml_sar(sample_data_pyAISm):
    """Test converting AIS to CoT for a SAR vessel."""
    sample_data_pyAISm["mmsi"] = "303862000"
    cot = ais_to_cot_xml(sample_data_pyAISm)

    assert cot.tag == "event"
    assert cot.attrib["type"] == "a-f-S-X-L"


def test_ais_to_cot_xml_crs(sample_data_pyAISm):
    """Test converting AIS to CoT for a CRS vessel."""
    sample_data_pyAISm["mmsi"] = "3669123"
    cot = ais_to_cot_xml(sample_data_pyAISm)

    assert cot.tag == "event"
    assert cot.attrib["type"] == "a-f-G-I-U-T"


def test_ais_to_cot(sample_data_pyAISm):
    """Test converting AIS to CoT."""
    cot: bytes = ais_to_cot(sample_data_pyAISm)
    assert b"a-f-S-X-M" in cot
    assert b"MMSI-366892000" in cot
