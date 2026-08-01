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

"""Tests for the AISCOT runtime status surface.

These assert what an operator would actually read off the Cockpit panel: that
a receiver hearing vessel names but plotting nothing looks different from a
dead antenna, and that a filter eating the traffic is visible as a filter.

The AISWorker coroutines are driven with asyncio.run() rather than
pytest-asyncio, which is not installed here. Bare `async def` tests are
SKIPPED by pytest while still being counted in the run -- tests that cannot
fail. These must be able to.
"""

import asyncio
import json
import os

from configparser import ConfigParser

import pytest

import pytak

import aiscot
import aiscot.classes
import aiscot.pyAISm
from aiscot.classes import AISNetworkClient, AISWorker

# A Type 1 position report, as pyAISm decodes it. speed is raw tenths of a
# knot, so 64 = 6.4kt: under way.
MSG_POSITION = {
    "type": 1,
    "mmsi": 366892000,
    "lat": 37.8169,
    "lon": -122.5121,
    "speed": 64,
    "heading": 95,
    "status": 0,
}

# Type 5 Static & Voyage data: the vessel's name and type, and no position at
# all. On RF this is where every ship name comes from.
MSG_STATIC = {
    "type": 5,
    "mmsi": 366892000,
    "shipname": "DELORES",
    "shiptype": 52,
}

# What pyAISm returns for the first half of a multi-line sentence.
MSG_PARTIAL = {"none": "empty"}

# A moored hull: position, but SOG zero and nav status 5.
MSG_MOORED = {
    "type": 1,
    "mmsi": 366892000,
    "lat": 37.8169,
    "lon": -122.5121,
    "speed": 0,
    "status": 5,
}


needs_statuswriter = pytest.mark.skipif(
    not hasattr(pytak, "StatusWriter"),
    reason="installed pytak predates StatusWriter",
)

# Separate from the above: aiscot has required pytak >= 7.3.12 for
# pytak.cot_event() since long before StatusWriter existed, so a pytak old
# enough to lack it cannot build CoT at all. Tests that need a real CoT event
# say so, rather than failing for a reason unrelated to status.
needs_cot_event = pytest.mark.skipif(
    not hasattr(pytak, "cot_event"),
    reason="installed pytak predates pytak.cot_event (aiscot needs >= 7.3.12)",
)


def _config(**overrides):
    # DEBUG is always present because pytak.Worker treats a falsy config as
    # "no config given" and substitutes a plain dict -- and an EMPTY
    # SectionProxy is falsy. A section with a key in it stays a SectionProxy,
    # which is what AISWorker's .getboolean() calls need.
    parser = ConfigParser()
    parser.read_dict({"aiscot": {"DEBUG": "false", **overrides}})
    return parser["aiscot"]


def _writer(tmp_path):
    return pytak.StatusWriter("aiscot-test", path=str(tmp_path / "status.json"))


def _in_loop(fn):
    """Run `fn()` inside a fresh event loop and return its result.

    Everything that constructs an asyncio.Queue or asyncio.Event goes through
    here. Those bind to the current event loop on Python < 3.10, and
    asyncio.run() leaves no current loop behind when it returns -- so building
    them at test-body level works on 3.13 and then fails in CI on 3.9 with
    "There is no current event loop", in whichever test happens to run after
    the first asyncio.run(). Building inside the loop is portable across
    3.9-3.13 and not order-dependent.

    `fn` may return a coroutine, which is awaited.
    """

    async def _main():
        result = fn()
        if asyncio.iscoroutine(result):
            return await result
        return result

    return asyncio.run(_main())


def _doc(status):
    with open(status.path, encoding="utf-8") as handle:
        return json.load(handle)


@needs_statuswriter
class TestNetworkStatusSurface:
    """The RF/NMEA path -- where every AryaOS box's AIS traffic lands."""

    def _client(self, tmp_path, action=None, **overrides):
        """Build a client and run `action(client)` inside one event loop."""
        built = {}

        def _make():
            client = AISNetworkClient(
                asyncio.Event(),
                asyncio.Queue(),
                _config(**overrides),
                _writer(tmp_path),
            )
            built["client"] = client
            if action is not None:
                action(client)

        _in_loop(_make)
        return built["client"]

    def test_position_report_is_marked_placed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: dict(MSG_POSITION))
        client = self._client(tmp_path, lambda c: c.handle_message(b"!AIVDM,mock"))

        doc = _doc(client.status)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["emitted"] == 1
        entry = doc["recent"][0]
        assert entry["mmsi"] == "366892000"
        assert entry["speed"] == 64
        assert entry["placed"] is True
        assert not client.queue.empty()

    def test_static_data_still_appears_in_the_feed(self, tmp_path, monkeypatch):
        """Hearing a vessel NAME is proof the receiver works.

        Type 5 plots nothing. If the feed showed only plotted vessels, a
        receiver pulling names off the water all day would render an empty
        panel -- which an operator reads as a fault and starts swapping
        antennas over.
        """
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: dict(MSG_STATIC))
        client = self._client(tmp_path, lambda c: c.handle_message(b"!AIVDM,mock"))

        doc = _doc(client.status)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["no_position"] == 1
        assert "emitted" not in doc["counters"]
        entry = doc["recent"][0]
        assert entry["shipname"] == "DELORES"
        assert entry["type"] == 52
        assert entry["placed"] is False
        assert doc["tracked"] == 1

    def test_partial_sentence_counted_but_not_shown_as_a_contact(
        self, tmp_path, monkeypatch
    ):
        """Half of a multi-line sentence: heard, but not yet a vessel."""
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: dict(MSG_PARTIAL))
        client = self._client(tmp_path, lambda c: c.handle_message(b"!AIVDM,mock"))

        doc = _doc(client.status)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["no_position"] == 1
        assert doc["recent"] == []

    def test_undecodable_sentence_is_not_counted_as_received(self, tmp_path):
        """A real bad sentence, not a mock: pyAISm raises on a non-AIVDM line.

        Before this change that exception escaped datagram_received() into
        asyncio's handler. Corrupt bursts are routine on RF AIS, so it must
        not be an error path -- but it must not inflate `rx` either, or a
        mis-wired feed of pure garbage would read as healthy traffic.
        """
        client = self._client(
            tmp_path, lambda c: c.handle_message(b"$GPGGA,not-an-ais-sentence")
        )
        assert not os.path.exists(client.status.path)

    def test_bad_checksum_is_not_counted_as_received(self, tmp_path):
        """Same, for the far more common failure: a corrupted payload."""
        client = self._client(
            tmp_path,
            lambda c: c.handle_message(
                b"!AIVDM,1,1,,B,177KQJ5000G?tO`K>RA1wUbN0TKH,0*00"
            ),
        )
        assert not os.path.exists(client.status.path)

    def test_known_craft_filter_is_visible_as_a_filter(self, tmp_path, monkeypatch):
        """"Why do I only see four ships" must be answerable from the UI."""
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: dict(MSG_POSITION))

        def _filtered(client):
            client.known_craft_db = {"999999999": {"MMSI": "999999999"}}
            client.handle_message(b"!AIVDM,mock-position")

        client = self._client(tmp_path, _filtered, INCLUDE_ALL_CRAFT="false")

        doc = _doc(client.status)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["filtered_unknown"] == 1
        assert "emitted" not in doc["counters"]

    def test_underway_only_drop_is_distinct_from_a_missing_position(
        self, tmp_path, monkeypatch
    ):
        """A moored hull was heard AND located; it was config that dropped it.

        Counted separately from `no_position` because the fix is a different
        knob: UNDERWAY_ONLY, not the antenna.
        """
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: dict(MSG_MOORED))
        client = self._client(
            tmp_path, lambda c: c.handle_message(b"!AIVDM,mock"), UNDERWAY_ONLY="true"
        )

        doc = _doc(client.status)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["no_cot"] == 1
        assert "no_position" not in doc["counters"]
        assert doc["recent"][0]["placed"] is False
        assert client.queue.empty()

    def test_cached_static_data_reaches_the_plotted_contact(
        self, tmp_path, monkeypatch
    ):
        """Static-then-position: the feed row for the plot carries the name."""
        msgs = iter([dict(MSG_STATIC), dict(MSG_POSITION)])
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: next(msgs))

        def _both(client):
            client.handle_message(b"!AIVDM,mock-static")
            client.handle_message(b"!AIVDM,mock-position")

        client = self._client(tmp_path, _both)

        # Writes are rate-limited to once a second, so two sentences in the
        # same second leave the file holding the first one's figures. That is
        # by design -- a busy channel must not spend its time serialising JSON
        # -- and the run loop's 5s heartbeat is what reconciles it. Forcing the
        # write here stands in for that heartbeat.
        client.status.write(force=True)
        doc = _doc(client.status)
        assert doc["counters"]["rx"] == 2
        assert doc["counters"]["emitted"] == 1
        assert doc["recent"][-1]["shipname"] == "DELORES"
        assert doc["recent"][-1]["placed"] is True


@needs_statuswriter
class TestFeedStatusSurface:
    """The HTTP feed path: AISHub / SeaVision."""

    def _worker(self, tmp_path, action=None, **overrides):
        """Build a worker and run `action(worker)` inside one event loop."""
        built = {}

        async def _make():
            worker = AISWorker(asyncio.Queue(), _config(**overrides))
            worker.status = _writer(tmp_path)
            built["worker"] = worker
            if action is not None:
                await action(worker)

        _in_loop(_make)
        return built["worker"]

    def test_feed_vessel_is_recorded_and_emitted(self, tmp_path):
        worker = self._worker(
            tmp_path, lambda w: w._process_message(dict(MSG_POSITION))
        )

        doc = _doc(worker.status)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["emitted"] == 1
        assert doc["recent"][0]["mmsi"] == "366892000"
        assert doc["recent"][0]["placed"] is True

    def test_record_without_mmsi_is_not_counted_as_received(self, tmp_path):
        """No MMSI is not a vessel report."""
        worker = self._worker(
            tmp_path, lambda w: w._process_message({"lat": 37.8, "lon": -122.5})
        )
        assert not os.path.exists(worker.status.path)

    def test_tracked_reports_vessels_in_the_current_feed(self, tmp_path):
        second = dict(MSG_POSITION)
        second["mmsi"] = 366999000
        worker = self._worker(
            tmp_path, lambda w: w.handle_data([dict(MSG_POSITION), second])
        )

        worker.status.write(force=True)  # stands in for the 5s heartbeat
        doc = _doc(worker.status)
        assert doc["tracked"] == 2
        assert doc["counters"]["rx"] == 2
        assert doc["counters"]["emitted"] == 2

    def test_worker_publishes_under_the_package_name_and_version(self):
        """Consumers read /run/aiscot/status.json by that exact name.

        Get the app name wrong and the gateway writes a status file nobody is
        watching, which presents identically to writing none at all.
        """
        worker = _in_loop(lambda: AISWorker(asyncio.Queue(), _config()))
        assert worker.status.app_name == "aiscot"
        assert worker.status.version == aiscot.__version__
        assert worker.status.path.endswith(os.path.join("aiscot", "status.json"))


class TestStatusDegradesVisibly:
    """A pytak without StatusWriter must not take the gateway down.

    The fleet runs pytak 7.3.13, which has no StatusWriter at all, so this is
    the path most boxes take today -- not a theoretical fallback.
    """

    def test_no_op_status_when_pytak_is_too_old(self, monkeypatch):
        monkeypatch.setattr(aiscot.classes, "_StatusWriter", None)
        status = aiscot.classes.make_status("aiscot", "0.1.0")

        # Every call the gateway makes must be safe on the stand-in.
        status.count("rx")
        status.record(mmsi="366892000", placed=True)
        status.set(tracked=1)
        assert status.write() is False

    @needs_cot_event
    def test_network_client_still_emits_cot_without_a_status_writer(self, monkeypatch):
        """The gateway's job is CoT, not telemetry. Losing one keeps the other.

        Constructed with no status argument at all, which is also what any
        third-party caller of AISNetworkClient() gets.
        """
        monkeypatch.setattr(aiscot.classes, "_StatusWriter", None)
        monkeypatch.setattr(aiscot.pyAISm, "decod_ais", lambda _: dict(MSG_POSITION))

        def _make():
            client = AISNetworkClient(asyncio.Event(), asyncio.Queue(), _config())
            client.handle_message(b"!AIVDM,mock-position")
            return client

        client = _in_loop(_make)
        assert isinstance(client.status, aiscot.classes._NoStatus)
        assert not client.queue.empty()

    @needs_cot_event
    def test_worker_still_emits_cot_without_a_status_writer(self, monkeypatch):
        monkeypatch.setattr(aiscot.classes, "_StatusWriter", None)

        sent = []
        seen = {}

        async def _main():
            worker = AISWorker(asyncio.Queue(), _config())
            seen["status"] = worker.status

            async def _capture(event):
                sent.append(event)

            worker.put_queue = _capture
            await worker._process_message(dict(MSG_POSITION))

        _in_loop(_main)
        assert isinstance(seen["status"], aiscot.classes._NoStatus)
        assert len(sent) == 1

    def test_real_writer_used_when_available(self):
        if aiscot.classes._StatusWriter is None:
            pytest.skip("installed pytak has no StatusWriter")
        assert not isinstance(
            aiscot.classes.make_status("x", "0"), aiscot.classes._NoStatus
        )
