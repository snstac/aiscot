#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Function Tests."""

import asyncio
import csv
import io
import urllib
import xml.etree.ElementTree

import pytest

import aiscot

import aiscot.functions


__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2021 Orion Labs, Inc."
__license__ = "Apache License, Version 2.0"


@pytest.fixture
def sample_data_libais():
    return {
        'id': 1,
        'repeat_indicator': 0,
        'mmsi': 211433000,
        'nav_status': 0,
        'rot_over_range': True,
        'rot': -731.386474609375,
        'sog': 1.100000023841858,
        'position_accuracy': 1,
        'x': -122.65529333333333,
        'y': 37.72890666666667,
        'cog': 80.30000305175781,
        'true_heading': 511,
        'timestamp': 25,
        'special_manoeuvre': 0,
        'spare': 0,
        'raim': True,
        'sync_state': 0,
        'slot_timeout': 3,
        'received_stations': 133,
        'nmea': '!AIVDM,1,1,,B,139`n:0P0;o>Qm@EUc838wvj2<25,0*4E\n'
    }


@pytest.fixture
def sample_data_pyAISm():
    return {
        "type": 3,
        "repeat": 0,
        "mmsi": 366892000,
        "status": 0,
        "turn": 0,
        "speed": 64,
        "accuracy": '1',
        "lon": -122.51208,
        "lat": 37.81691333333333,
        "course": 97.10000000000001,
        "heading": 95,
        "second": 9,
        "maneuver": 0,
        "raim": '0',
        "radio": 11729
    }


def test_ais_to_cot(sample_data_pyAISm):
    cot = aiscot.functions.ais_to_cot_xml(sample_data_pyAISm)
    assert isinstance(cot, xml.etree.ElementTree.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-n-S-X-M"
    assert cot.attrib["uid"] == "MMSI-366892000"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.81691333333333"
    assert point[0].attrib["lon"] == "-122.51208"
    assert point[0].attrib["hae"] == "9999999.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"
    assert detail[0].attrib["uid"] == "MMSI-366892000"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "95"
    assert track[0].attrib["speed"] == "32.924416"