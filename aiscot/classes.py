#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Greg Albrecht <oss@undef.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author:: Greg Albrecht W2GMD <oss@undef.net>
#

"""AISCOT Class Definitions."""

import asyncio
import logging

from configparser import ConfigParser

import aiohttp

import pytak
import aiscot
import aiscot.pyAISm

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


# pylint: disable=too-many-instance-attributes
class AISNetworkClient(asyncio.Protocol):

    """Class for handling connections from network AIS feed."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aiscot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aiscot.LOG_LEVEL)
        _console_handler.setFormatter(aiscot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger("asyncio").setLevel(aiscot.LOG_LEVEL)

    def __init__(self, ready, queue, config) -> None:
        self.transport = None
        self.address = None
        self.known_craft_db = None

        self.ready = ready
        self.queue = queue
        self.config = config

        if self.config.getboolean("DEBUG", False):
            _ = [x.setLevel(logging.DEBUG) for x in self._logger.handlers]

    def handle_message(self, data) -> None:
        """Handles incoming AIS data from network."""
        d_data = data.decode().strip()
        msg = aiscot.pyAISm.decod_ais(d_data)

        self._logger.debug("Decoded AIS: '%s'", msg)

        mmsi = str(msg.get("mmsi"))

        known_craft = {}

        if self.known_craft_db:
            known_craft = (
                list(
                    filter(
                        lambda x: x["MMSI"].strip().upper() == mmsi,
                        self.known_craft_db,
                    )
                )
                or [{}]
            )[0]
            # self._logger.debug("known_craft='%s'", known_craft)

        # Skip if we're using known_craft CSV and this Craft isn't found:
        if (
            self.known_craft_db
            and not known_craft
            and not self.config.getboolean("INCLUDE_ALL_CRAFT")
        ):
            return

        event: str = aiscot.ais_to_cot(msg, config=self.config, known_craft=known_craft)

        if event:
            self.queue.put_nowait(event)

    def connection_made(self, transport):
        """Called when a network connection is made."""
        self.transport = transport
        self.address = transport.get_extra_info("peername")
        self._logger.info("Connection from %s", self.address)

        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aiscot.read_known_craft(known_craft)
        self.ready.set()

    def datagram_received(self, data, addr):
        """Called when a UDP datagram is received."""
        self._logger.debug("Recieved from %s: '%s'", addr, data)
        for line in data.splitlines():
            self.handle_message(line)

    def connection_lost(self, exc):
        """Called when a network connection is lost."""
        self.ready.clear()
        self._logger.exception(exc)
        self._logger.warning("Disconnected from %s", self.address)


class AISWorker(pytak.QueueWorker):

    """AIS Cursor-on-Target Class."""

    def __init__(self, queue: asyncio.Queue, config: ConfigParser) -> None:
        super().__init__(queue, config)
        _ = [x.setFormatter(aiscot.LOG_FORMAT) for x in self._logger.handlers]
        self.known_craft_db = None

    async def handle_data(self, data) -> None:
        """Handles received MMSI data."""
        # self._logger.info("Received AIS: '%s'", msg)
        mmsi = None

        for msg in data:
            mmsi = str(msg.get("MMSI"))

            known_craft = {}

            if self.known_craft_db:
                known_craft = (
                    list(
                        filter(
                            lambda x: x["MMSI"].strip().upper() == mmsi,
                            self.known_craft_db,
                        )
                    )
                    or [{}]
                )[0]
                # self._logger.debug("known_craft='%s'", known_craft)

            # Skip if we're using known_craft CSV and this Craft isn't found:
            if (
                self.known_craft_db
                and not known_craft
                and not self.config.getboolean("INCLUDE_ALL_CRAFT")
            ):
                continue

            event: str = aiscot.ais_to_cot(msg, self.config, known_craft=known_craft)
            await self.put_queue(event)

    async def get_aishub_feed(self, session: aiohttp.ClientSession, feed_url) -> None:
        """
        Gets AIS data from AISHub feed.
        """
        response = await session.request(method="GET", url=feed_url)
        response.raise_for_status()
        json_resp = await response.json()

        api_report = json_resp[0]
        if api_report.get("ERROR"):
            self._logger.error("AISHub.com API returned an error: ")
            self._logger.error(api_report)
        else:
            ships = json_resp[1]
            self._logger.debug("Retrieved %s ships", len(ships))
            await self.handle_data(ships)

    async def run(self, number_of_iterations=-1) -> None:
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info("Sending to: %s", self.config.get("COT_URL"))

        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aiscot.read_known_craft(known_craft)

        aishub_url = self.config.get("AISHUB_URL")
        if aishub_url:
            poll_interval: int = int(
                self.config.get("POLL_INTERVAL") or aiscot.DEFAULT_POLL_INTERVAL
            )
            async with aiohttp.ClientSession() as session:
                while 1:
                    await asyncio.sleep(poll_interval)
                    self._logger.info(
                        "Polling every %ss: %s", poll_interval, aishub_url
                    )
                    await self.get_aishub_feed(session, aishub_url)
        else:
            port: int = int(self.config.get("LISTEN_PORT", aiscot.DEFAULT_LISTEN_PORT))
            host: str = self.config.get("LISTEN_HOST", aiscot.DEFAULT_LISTEN_HOST)

            loop = asyncio.get_event_loop()
            ready = asyncio.Event()
            self._logger.info("Listening for AIS on %s:%s", host, port)
            await loop.create_datagram_endpoint(
                lambda: AISNetworkClient(ready, self.queue, self.config),
                local_addr=(host, port),
            )
            await ready.wait()
            while 1:
                await asyncio.sleep(0.01)
