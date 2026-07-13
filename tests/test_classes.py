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

"""AISCOT AISNetworkClient tests."""

import asyncio

from configparser import ConfigParser

import aiscot
import aiscot.classes
import aiscot.pyAISm


def _make_client():
    parser = ConfigParser()
    parser.add_section("aiscot")
    return aiscot.classes.AISNetworkClient(
        asyncio.Event(), asyncio.Queue(), parser["aiscot"]
    )


def test_network_client_static_cache(monkeypatch):
    """Type 5 static data (no position) is cached per MMSI and merged into
    the vessel's subsequent position reports, so ship-class styling and
    name prefixes work on RF/NMEA feeds."""
    client = _make_client()
    msgs = iter(
        [
            # Type 5 Static & Voyage data: name + ship type, no position.
            {"type": 5, "mmsi": 366892000, "shipname": "DELORES", "shiptype": 52},
            # Type 1 position report: no name/ship type.
            {
                "type": 1,
                "mmsi": 366892000,
                "lat": 37.8169,
                "lon": -122.5121,
                "speed": 64,
                "heading": 95,
                "status": 0,
            },
        ]
    )
    monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: next(msgs))

    client.handle_message(b"!AIVDM,mock-static")
    assert client.queue.empty()  # static data alone emits no CoT

    client.handle_message(b"!AIVDM,mock-position")
    event = client.queue.get_nowait()
    # Cached shipname + shiptype applied: prefixed callsign, tug class.
    assert b'callsign="T/B DELORES"' in event


def test_network_client_static_cache_bounded(monkeypatch):
    """The static cache is FIFO-bounded."""
    client = _make_client()
    monkeypatch.setattr(aiscot.classes, "STATIC_CACHE_MAX", 3)
    for n in range(5):
        msg = {"type": 5, "mmsi": 366892000 + n, "shipname": f"BOAT {n}"}
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _, m=msg: m)
        client.handle_message(b"!AIVDM,mock")
    assert len(client._static_cache) == 3
    assert "366892004" in client._static_cache
    assert "366892000" not in client._static_cache
