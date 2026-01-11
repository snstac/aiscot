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

from configparser import ConfigParser
from typing import Any, List, Optional

import aiohttp

import pytak
import aiscot
import aiscot.pyAISm


# pylint: disable=too-many-instance-attributes
class AISNetworkClient(asyncio.Protocol):
    """Network AIS feed client (receiver)."""

    __slots__ = ('transport', 'address', 'known_craft_db', 'ready', 'queue', 'config', '_include_all_craft', '_debug')

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pytak.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pytak.LOG_LEVEL)
        _console_handler.setFormatter(pytak.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger("asyncio").setLevel(pytak.LOG_LEVEL)

    def __init__(self, ready, queue, config) -> None:
        """Initialize this class."""
        self.transport = None
        self.address = None
        self.known_craft_db: Optional[dict] = None

        self.ready = ready
        self.queue = queue
        self.config = config

        # Cache config values to avoid repeated parsing
        self._debug = self.config.getboolean("DEBUG", False)
        self._include_all_craft = self.config.getboolean("INCLUDE_ALL_CRAFT", False)

        if self._debug:
            for handler in self._logger.handlers:
                handler.setLevel(logging.DEBUG)

    def handle_message(self, data: bytes) -> None:
        """Handle incoming AIS data from network."""
        d_data = data.decode().strip()
        msg: dict = aiscot.pyAISm.decod_ais(d_data)

        if self._debug:
            self._logger.debug("Decoded AIS: '%s'", msg)

        mmsi = str(msg.get("mmsi", ""))

        known_craft: dict = {}

        if self.known_craft_db:
            known_craft = self.known_craft_db.get(mmsi, {})

        # Skip if we're using known_craft CSV and this Craft isn't found:
        if self.known_craft_db and not known_craft and not self._include_all_craft:
            return

        event: Optional[bytes] = aiscot.cot_to_xml(
            msg, config=self.config, known_craft=known_craft
        )

        if event:
            self.queue.put_nowait(event)

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

    __slots__ = ('known_craft_db', 'session', 'feed_url', '_include_all_craft', '_poll_interval', '_host', '_port')

    def __init__(self, queue: asyncio.Queue, config: ConfigParser) -> None:
        """Initialize an instance of this class."""
        super().__init__(queue, config)
        _ = [x.setFormatter(pytak.LOG_FORMAT) for x in self._logger.handlers]
        self.known_craft_db: dict = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.feed_url: Optional[str] = None
        
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

        for msg in data:
            await self._process_message(msg)

    async def _process_message(self, msg: dict) -> None:
        """Process a single AIS message."""
        # Use .get() with chained fallback for MMSI
        mmsi = msg.get("MMSI") or msg.get("mmsi")
        if not mmsi:
            return
        mmsi = str(mmsi)

        known_craft: dict = {}

        if self.known_craft_db:
            known_craft = self.known_craft_db.get(mmsi, {})
            if known_craft:
                self._logger.debug("known_craft='%s'", known_craft)

        # Skip if we're using known_craft CSV and this Craft isn't found:
        if self.known_craft_db and not known_craft and not self._include_all_craft:
            return

        event: Optional[bytes] = aiscot.cot_to_xml(
            msg, self.config, known_craft=known_craft
        )

        if event:
            await self.put_queue(event)

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
        await self._initialize_feed()

    async def _initialize_feed(self) -> None:
        """Initialize the feed URL and start polling or network receiver."""
        self.feed_url = self.config.get("FEED_URL")
        self._logger.info("Using FEED_URL: %s", self.feed_url)
        if self.feed_url:
            await self._poll_feed()
        else:
            await self._network_rx()

    async def _network_rx(self) -> None:
        """Start an AIS network receiver."""
        loop = asyncio.get_event_loop()
        ready = asyncio.Event()

        self._logger.info("Listening for AIS on %s:%s", self._host, self._port)

        await loop.create_datagram_endpoint(
            lambda: AISNetworkClient(ready, self.queue, self.config),
            local_addr=(self._host, self._port),
        )
        await ready.wait()
        # Keep the coroutine alive without spinning the CPU
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour, will wake on events

    async def _poll_feed(self) -> None:
        """Poll a feed URL for AIS data."""
        async with aiohttp.ClientSession() as self.session:
            while 1:
                self._logger.info("Polling every %ss: %s", self._poll_interval, self.feed_url)
                await self._get_feed()
                await asyncio.sleep(self._poll_interval)
