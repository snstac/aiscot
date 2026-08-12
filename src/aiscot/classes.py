#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# classes.py from https://github.com/snstac/aiscot
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

"""AISCOT Class Definitions."""

import asyncio
import logging
import xml.etree.ElementTree as ET

from configparser import ConfigParser
from typing import Any, List, Optional

import aiohttp

import pytak
import aiscot
import aiscot.pyAISm

try:
    import gpsd as _gpsd
except ImportError:
    _gpsd = None


# Static & Voyage data (Type 5/19/24) arrives in separate messages from
# position reports on the NMEA path; cache it per MMSI so ship-class
# styling and name prefixes work on RF feeds. Bounded FIFO.
STATIC_CACHE_MAX = 4096
_STATIC_KEYS = ("shipname", "shiptype", "callsign")


class _NoStatus:
    """Stand-in for pytak.StatusWriter on a pytak too old to have one.

    AryaOS boxes are updated as packages, so this gateway can land on a host
    whose pytak predates StatusWriter (added in 7.4.0) -- the fleet is on
    7.3.13 today. Failing to import would take the gateway down over its
    telemetry helper, which is exactly backwards: moving CoT is the job,
    reporting on it is not.

    Degrading here is safe because it is VISIBLE. With nothing writing
    /run/aiscot/status.json, the Cockpit plugin reports "no status from this
    gateway ... may be running a pytak too old to report status" rather than
    rendering an empty feed as though the water were empty.
    """

    def count(self, *args, **kwargs) -> None:
        return None

    def record(self, *args, **kwargs) -> None:
        return None

    def set(self, *args, **kwargs) -> None:
        return None

    def write(self, *args, **kwargs) -> bool:
        return False


# Resolved at import so a missing StatusWriter is a startup-time decision
# rather than an AttributeError on the first sentence off the wire.
_StatusWriter = getattr(pytak, "StatusWriter", None)


def make_status(app_name: str, version: str):
    """Return a status writer, or a no-op if this pytak has none."""
    if _StatusWriter is None:
        return _NoStatus()
    return _StatusWriter(app_name, version=version)


# pylint: disable=too-many-instance-attributes
class AISNetworkClient(asyncio.Protocol):
    """Network AIS feed client (receiver)."""

    __slots__ = ('transport', 'address', 'known_craft_db', 'ready', 'queue', 'config', '_include_all_craft', '_debug', '_static_cache', 'status')

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pytak.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pytak.LOG_LEVEL)
        _console_handler.setFormatter(pytak.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger("asyncio").setLevel(pytak.LOG_LEVEL)

    def __init__(self, ready, queue, config, status=None) -> None:
        """Initialize this class."""
        self.transport = None
        self.address = None
        self.known_craft_db: Optional[dict] = None
        self._static_cache: dict = {}

        self.ready = ready
        self.queue = queue
        self.config = config

        # Shares the owning AISWorker's status writer, because on an RF/NMEA
        # deployment this class is where all the traffic actually lands -- the
        # worker only sets up the socket. Optional so the protocol stays
        # constructible on its own.
        self.status = status if status is not None else _NoStatus()

        # Cache config values to avoid repeated parsing
        self._debug = self.config.getboolean("DEBUG", False)
        self._include_all_craft = self.config.getboolean("INCLUDE_ALL_CRAFT", False)

        if self._debug:
            for handler in self._logger.handlers:
                handler.setLevel(logging.DEBUG)

    def handle_message(self, data: bytes) -> None:
        """Handle incoming AIS data from network."""
        try:
            d_data = data.decode().strip()
            msg: dict = aiscot.pyAISm.decod_ais(d_data)
        except Exception as exc:  # noqa: BLE001 -- see below
            # decod_ais raises on a bad checksum or a non-AIVDM line, and RF
            # AIS produces broken sentences constantly. Previously this
            # propagated out of datagram_received() into asyncio's exception
            # handler, which logged a traceback per corrupt burst. Counted
            # instead of raised -- but deliberately NOT counted as `rx`, so a
            # mis-wired feed of pure garbage cannot look like healthy traffic.
            self._logger.debug("Undecodable AIS sentence (%s bytes): %s", len(data), exc)
            return

        if not msg:
            return

        if self._debug:
            self._logger.debug("Decoded AIS: '%s'", msg)

        self.status.count("rx")

        mmsi = str(msg.get("mmsi", ""))

        # Position-less messages (Type 5/24 Static & Voyage data, partial
        # multi-line sentences) produce no CoT — but their shipname/shiptype
        # is what ship-class styling needs, so cache it per MMSI and fold it
        # into this vessel's subsequent position reports.
        if "lat" not in msg:
            # The COMMON case on RF, not an error: Type 5 static data is how a
            # vessel gets its name, and multi-line sentences arrive in halves.
            self.status.count("no_position")
            if mmsi:
                static = {
                    k: msg[k] for k in _STATIC_KEYS if msg.get(k) not in (None, "")
                }
                if static:
                    self._static_cache.setdefault(mmsi, {}).update(static)
                    while len(self._static_cache) > STATIC_CACHE_MAX:
                        self._static_cache.pop(next(iter(self._static_cache)))
                    # Shown in the feed even though it plots nothing: hearing a
                    # vessel name is proof the receiver is working, and on a
                    # quiet stretch of water it may be the only traffic there
                    # is. An empty panel would read as a dead antenna.
                    self.status.record(
                        mmsi=mmsi,
                        shipname=static.get("shipname"),
                        type=static.get("shiptype"),
                        placed=False,
                    )
                    self.status.set(tracked=len(self._static_cache))
            self.status.write()
            return
        if mmsi in self._static_cache:
            msg = {**self._static_cache[mmsi], **msg}

        known_craft: dict = {}

        if self.known_craft_db:
            known_craft = self.known_craft_db.get(mmsi, {})

        # Skip if we're using known_craft CSV and this Craft isn't found:
        if self.known_craft_db and not known_craft and not self._include_all_craft:
            # "Why do I only see four ships" must be answerable from the UI,
            # and "because you configured a KNOWN_CRAFT filter" is the answer
            # often enough to be worth a counter.
            self.status.count("filtered_unknown")
            self.status.write()
            return

        event: Optional[bytes] = aiscot.cot_to_xml(
            msg, config=self.config, known_craft=known_craft
        )

        self.status.record(
            mmsi=mmsi,
            shipname=msg.get("shipname"),
            type=msg.get("shiptype"),
            speed=msg.get("speed"),
            placed=event is not None,
        )
        self.status.set(tracked=len(self._static_cache))

        if event:
            self.status.count("emitted")
            self.queue.put_nowait(event)
        else:
            # A positioned vessel that produced no CoT: UNDERWAY_ONLY dropped
            # a moored vessel, IGNORE_ATON dropped a navigation aid, or the
            # position failed validation. Distinct from `filtered_unknown`
            # because the fix is a different config knob.
            self.status.count("no_cot")

        self.status.write()

    def connection_made(self, transport) -> None:
        """Call when a network connection is made."""
        self.transport = transport
        self.address = transport.get_extra_info(
            "peername", "UDP peer (no peername available)."
        )
        self._logger.info("Connection from %s", self.address)

        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            craft_list = aiscot.get_known_craft(known_craft)
            # Convert to dict for O(1) lookups by MMSI with pre-normalized keys
            self.known_craft_db = {
                mmsi.strip().upper(): c
                for c in craft_list
                if (mmsi := c.get("MMSI"))
            }
        self.ready.set()

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        """Call when a UDP datagram is received."""
        if self._debug:
            self._logger.debug("Recieved from %s: '%s'", addr, data)
        for line in data.splitlines():
            self.handle_message(line)

    def connection_lost(self, exc) -> None:
        """Call when a network connection is lost."""
        self.ready.clear()
        self._logger.exception(exc)
        self._logger.warning("Disconnected from %s", self.address)


class AISWorker(pytak.QueueWorker):
    """AIS to TAK worker."""

    __slots__ = (
        "known_craft_db",
        "session",
        "feed_url",
        "_include_all_craft",
        "_poll_interval",
        "_host",
        "_port",
        "_transport",
        "status",
    )

    def __init__(self, queue: asyncio.Queue, config: ConfigParser) -> None:
        """Initialize an instance of this class."""
        super().__init__(queue, config)
        _ = [x.setFormatter(pytak.LOG_FORMAT) for x in self._logger.handlers]
        self.known_craft_db: dict = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.feed_url: Optional[str] = None
        self._transport = None

        # Runtime status for Cockpit. systemd gives us /run/aiscot via
        # RuntimeDirectory=, so this lands where the plugin looks for it.
        self.status = make_status("aiscot", aiscot.__version__)

        # Cache config values to avoid repeated parsing
        self._include_all_craft = self.config.getboolean("INCLUDE_ALL_CRAFT", False)
        self._poll_interval = int(self.config.get("POLL_INTERVAL", aiscot.DEFAULT_POLL_INTERVAL))
        self._host = self.config.get("LISTEN_HOST", aiscot.DEFAULT_LISTEN_HOST)
        self._port = int(self.config.get("LISTEN_PORT", aiscot.DEFAULT_LISTEN_PORT))

    async def handle_data(self, data: list) -> None:
        """Handle received data."""
        self._logger.debug("Handling Data: '%s'", data)
        if len(data) == 0:
            return

        # How many vessels this feed currently reports. A level, not a total:
        # "31 ships right now" is the number an operator sanity-checks a feed
        # against, and a lifetime `rx` count cannot answer it.
        self.status.set(tracked=len(data))

        for msg in data:
            await self._process_message(msg)

    async def _process_message(self, msg: dict) -> None:
        """Process a single AIS message."""
        # Use .get() with chained fallback for MMSI
        mmsi = msg.get("MMSI") or msg.get("mmsi")
        if not mmsi:
            # No MMSI is not a vessel report. Deliberately not counted as
            # received, so a malformed feed cannot look like healthy traffic.
            return
        mmsi = str(mmsi)

        self.status.count("rx")

        known_craft: dict = {}

        if self.known_craft_db:
            known_craft = self.known_craft_db.get(mmsi, {})
            if known_craft:
                self._logger.debug("known_craft='%s'", known_craft)

        # Skip if we're using known_craft CSV and this Craft isn't found:
        if self.known_craft_db and not known_craft and not self._include_all_craft:
            self.status.count("filtered_unknown")
            self.status.write()
            return

        event: Optional[bytes] = aiscot.cot_to_xml(
            msg, self.config, known_craft=known_craft
        )

        self.status.record(
            mmsi=mmsi,
            shipname=msg.get("shipname") or msg.get("NAME"),
            type=msg.get("shiptype") or msg.get("TYPE"),
            speed=msg.get("speed") or msg.get("SOG"),
            placed=event is not None,
        )

        if event:
            self.status.count("emitted")
            await self.put_queue(event)
        else:
            # UNDERWAY_ONLY / IGNORE_ATON / unusable position -- see the same
            # branch in AISNetworkClient.handle_message().
            self.status.count("no_cot")

        self.status.write()

    async def _get_feed(self) -> None:
        """Get AIS data from AIS URL feed."""
        if not self.session:
            raise ValueError("No HTTP session available.")

        if not self.feed_url:
            raise ValueError("FEED_URL is not set.")

        if "seavision" in self.feed_url:
            await self._get_feed_seavision()
        else:
            await self._get_feed_aishub()

    async def _get_feed_aishub(self) -> None:
        """Get AIS data from AISHub feed."""
        self._logger.info("Using AISHub.com API: %s", self.feed_url)

        response = await self.session.request(method="GET", url=self.feed_url)
        response.raise_for_status()
        json_resp = await response.json()

        if len(json_resp) < 2:
            self._logger.error("AISHub.com API response is not as expected.")
            self._logger.error(json_resp)
            return

        api_report = json_resp[0]
        if api_report.get("ERROR"):
            self._logger.error("AISHub.com API returned an error: ")
            self._logger.error(api_report)
        else:
            ships = json_resp[1]
            self._logger.debug("Retrieved %s ships", len(ships))
            await self.handle_data(ships)

    async def _get_feed_seavision(self) -> None:
        """Get AIS data from SeaVision feed."""
        self._logger.info("Using SeaVision API")
        headers = {
            "x-api-key": self.config.get("SEAVISION_API_KEY"),
            "accept": "application/json",
        }
        response = await self.session.request(
            method="GET", url=self.feed_url, headers=headers
        )
        response.raise_for_status()
        json_resp = await response.json()
        if json_resp:
            self._logger.debug("Retrieved %s ships", len(json_resp))
            await self.handle_data(json_resp)
        else:
            self._logger.error("No ships found in SeaVision API response.")

    async def _load_known_craft(self) -> None:
        """Load known craft database if available."""
        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            craft_list = aiscot.get_known_craft(known_craft)
            # Convert to dict for O(1) lookups by MMSI with pre-normalized keys
            self.known_craft_db = {
                mmsi.strip().upper(): c
                for c in craft_list
                if (mmsi := c.get("MMSI"))
            }

    async def run(self, number_of_iterations=-1) -> None:
        """Run this Thread, reads AIS & outputs CoT."""
        self._logger.info("Running %s", self.__class__.__name__)
        await self._load_known_craft()

        # Write once, before any vessel arrives. Without this the management
        # UI shows "no status from this gateway" until the first contact --
        # indistinguishable from a gateway that failed to start. AIS over RF
        # can be silent for many minutes on an inland or quiet-water site,
        # which is exactly when someone goes looking at the panel.
        self.status.write(force=True)

        heartbeat = asyncio.ensure_future(self._status_heartbeat())
        try:
            await self._initialize_feed()
        finally:
            heartbeat.cancel()
            await asyncio.gather(heartbeat, return_exceptions=True)

    async def _status_heartbeat(self, interval: float = 5.0) -> None:
        """Keep the status file fresh while no vessels are being heard.

        Quiet water and a wedged gateway both produce zero CoT. The UI tells
        them apart by whether this file keeps changing, so an idle-but-healthy
        gateway MUST keep writing.

        A separate task rather than a timer inside the feed loop: the RF path
        parks on a datagram socket with no period at all, and the API path's
        period is the operator's POLL_INTERVAL (often 30s+). Neither can
        provide a 5s heartbeat, and neither should be slowed down to try.
        """
        while True:
            await asyncio.sleep(interval)
            self.status.write(force=True)

    async def _initialize_feed(self) -> None:
        """Initialize the feed URL and start polling or network receiver."""
        self.feed_url = self.config.get("FEED_URL")
        self._logger.info("Using FEED_URL: %s", self.feed_url)
        if self.feed_url:
            self.status.set(feed=str(self.feed_url))
            await self._poll_feed()
        else:
            await self._network_rx()

    async def _network_rx(self) -> None:
        """Start an AIS network receiver."""
        loop = asyncio.get_event_loop()
        ready = asyncio.Event()

        self._logger.info("Listening for AIS on %s:%s", self._host, self._port)

        self.status.set(listen=f"udp://{self._host}:{self._port}")

        transport, _ = await loop.create_datagram_endpoint(
            lambda: AISNetworkClient(ready, self.queue, self.config, self.status),
            local_addr=(self._host, self._port),
        )
        self._transport = transport
        try:
            await ready.wait()

            # Re-write now that the socket is actually bound. run()'s startup
            # write happens before this point and so cannot name the listener;
            # without this the panel says "listening on: unknown" until the first
            # heartbeat, and "where is it listening" is the first question asked
            # when a feed shows nothing.
            self.status.write(force=True)

            # Keep the coroutine alive without spinning the CPU
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour, will wake on events
        finally:
            await self.close()

    async def close(self) -> None:
        """Release feed resources before PyTAK rebuilds this client.

        PyTAK reconnects in-process after a TAK transport outage. Without an
        explicit close hook the UDP listener survives cancellation until the
        event loop later collects it, so the replacement AISWorker can fail
        with EADDRINUSE on the same LISTEN_PORT.
        """
        transport, self._transport = self._transport, None
        if transport is not None:
            transport.close()
            await asyncio.sleep(0)
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def _poll_feed(self) -> None:
        """Poll a feed URL for AIS data."""
        async with aiohttp.ClientSession() as self.session:
            while 1:
                self._logger.info("Polling every %ss: %s", self._poll_interval, self.feed_url)
                await self._get_feed()
                await asyncio.sleep(self._poll_interval)


class SensorWorker(pytak.QueueWorker):
    """Periodic sensor CoT heartbeat. Sources position from gpsd, config, or null island."""

    async def run(self, _=-1) -> None:
        period = int(self.config.get(
            "SENSOR_KEEPALIVE_PERIOD", aiscot.DEFAULT_SENSOR_KEEPALIVE_PERIOD))
        self._logger.info(
            "Running SensorWorker (period=%ds, gpsd=%s)", period, _gpsd is not None)
        while True:
            lat, lon, hae, ce, le = await self._get_position()
            cot = aiscot.gen_sensor_cot(self.config, lat, lon, hae, ce, le)
            if cot is not None:
                await self.put_queue(ET.tostring(cot))
            await asyncio.sleep(period)

    async def _get_position(self):
        if _gpsd is not None:
            try:
                result = await asyncio.to_thread(self._poll_gpsd)
                if result is not None:
                    return result
            except Exception as exc:
                self._logger.debug("gpsd unavailable: %s", exc)
        lat = float(self.config.get("SENSOR_LAT") or aiscot.DEFAULT_SENSOR_LAT)
        lon = float(self.config.get("SENSOR_LON") or aiscot.DEFAULT_SENSOR_LON)
        hae = float(self.config.get("SENSOR_HAE") or aiscot.DEFAULT_SENSOR_HAE)
        return lat, lon, hae, "9999999.0", "9999999.0"

    @staticmethod
    def _poll_gpsd():
        _gpsd.connect()
        packet = _gpsd.get_current()
        if packet.mode < 2:
            return None
        try:
            lat, lon = packet.position()
        except Exception:
            return None
        try:
            hae = packet.altitude()
        except Exception:
            hae = 0.0
        ce = str(getattr(packet, "error", {}).get("x", "9999999.0") or "9999999.0")
        le = str(getattr(packet, "error", {}).get("v", "9999999.0") or "9999999.0")
        return lat, lon, hae, ce, le
