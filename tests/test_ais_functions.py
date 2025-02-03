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

"""AISCOT AIS Function Tests."""

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


def test_get_mid(sample_data_pyAISm):
    """Test that git_mid returns the country MID corresponding for a given MMSI."""
    mmsi = sample_data_pyAISm.get("mmsi")
    country = aiscot.ais_functions.get_mid(mmsi)
    assert country == "United States of America"


def test_get_known_craft():
    """Test reading know craft CSV with `aiscot.ais_functions.get_known_craft()`."""
    known_craft = aiscot.ais_functions.get_known_craft(
        "tests/data/test_known_craft.csv"
    )
    assert known_craft[0].get("MMSI") == "366892000"


def test_get_aton(sample_aton):
    """Test Aid to Naviation vessels with `aiscot.ais_functions.get_aton()`."""
    mmsi = sample_aton.get("mmsi")
    assert aiscot.ais_functions.get_aton(mmsi) is True


def test_get_crs():
    """Test CRS vessels with `aiscot.ais_functions.get_crs()`."""
    assert aiscot.ais_functions.get_crs("3669123") is True
    assert aiscot.ais_functions.get_crs("003369000") is True
    assert aiscot.ais_functions.get_crs("938852000") is False


def test_get_sar():
    """Test SAR vessels with `aiscot.ais_functions.get_sar()`."""
    assert aiscot.ais_functions.get_sar("111892000") is True
    assert aiscot.ais_functions.get_sar("303862000") is True
    assert aiscot.ais_functions.get_sar("338852000") is True
    assert aiscot.ais_functions.get_sar("938852000") is False


def test_get_shipname():
    """Test getting shipname from db using `aiscot.ais_functions.get_shipname()`."""
    assert aiscot.ais_functions.get_shipname("303990000") == "USCG EAGLE"
    assert aiscot.ais_functions.get_shipname("938852000") == ""
