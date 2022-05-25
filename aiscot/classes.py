#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""AIS Cursor-On-Target Class Definitions."""

import asyncio
import configparser
import logging
import urllib

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

    def __init__(self, ready, event_queue, opts) -> None:
        self.transport = None
        self.address = None

        self.ready = ready
        self.event_queue = event_queue

        self.cot_stale = opts.get("COT_STALE")
        self.cot_type = opts.get("COT_TYPE")

        self.include_all_craft = bool(opts.get("INCLUDE_ALL_CRAFT")) or False

        self.filters = opts.get("FILTERS")
        self.known_craft = opts.get("KNOWN_CRAFT")
        self.known_craft_key = opts.get("KNOWN_CRAFT_KEY") or "MMSI"

        self.filter_type = ""
        self.known_craft_db = None

    def handle_message(self, data) -> None:
        """Handles incoming AIS data from network."""
        d_data = data.decode().strip()
        msg = aiscot.pyAISm.decod_ais(d_data)

        # self._logger.info("Received AIS: '%s'", msg)

        mmsi = str(msg.get("mmsi"))

        known_craft = {}

        if self.filter_type:
            if self.filter_type == "MMSI":
                filter_key: str = str(mmsi)
            else:
                filter_key: str = ""

            # self._logger.debug("filter_key=%s", filter_key)

            if self.known_craft_db and filter_key:
                known_craft = (
                    list(
                        filter(
                            lambda x: x[self.known_craft_key].strip().upper()
                            == filter_key,
                            self.known_craft_db,
                        )
                    )
                    or [{}]
                )[0]
                # self._logger.debug("known_craft='%s'", known_craft)
            elif filter_key:
                if "include" in self.filters[
                    self.filter_type
                ] and filter_key not in self.filters.get(self.filter_type, "include"):
                    return
                if "exclude" in self.filters[
                    self.filter_type
                ] and filter_key in self.filters.get(self.filter_type, "exclude"):
                    return

        # If we're using a known_craft csv and this craft wasn't found, skip:
        if self.known_craft_db and not known_craft and not self.include_all_craft:
            return

        event: str = aiscot.ais_to_cot(
            msg, stale=self.cot_stale, cot_type=self.cot_type, known_craft=known_craft
        )

        if event:
            self.event_queue.put_nowait(event)

    def connection_made(self, transport):
        """Called when a network connection is made."""
        self.transport = transport
        self.address = transport.get_extra_info("peername")
        self._logger.debug("Connection from %s", self.address)

        if self.known_craft is not None:
            self._logger.info("Using KNOWN_CRAFT File: '%s'", self.known_craft)
            self.known_craft_db = aiscot.read_known_craft(self.known_craft)
            self.filters = configparser.ConfigParser()
            self.filters.add_section(self.known_craft_key)
            self.filters[self.known_craft_key]["include"] = str(
                [x[self.known_craft_key].strip().upper() for x in self.known_craft_db]
            )

        if self.filters or self.known_craft_db:
            filter_src = self.filters or self.known_craft_key
            self._logger.debug("filter_src=%s", filter_src)
            if filter_src:
                if "MMSI" in filter_src:
                    self.filter_type = "MMSI"
                self._logger.debug("filter_type=%s", self.filter_type)

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


class AISWorker(pytak.MessageWorker):

    """AIS Cursor-on-Target Class."""

    def __init__(self, event_queue: asyncio.Queue, config) -> None:
        super().__init__(event_queue)

        self.config = config["aiscot"]

        aishub_url = self.config.get("AISHUB_URL")
        if aishub_url:
            self.aishub_url: urllib.parse.ParseResult = urllib.parse.urlparse(
                aishub_url
            )
        else:
            self.aishub_url = None

        self.cot_stale = self.config.get("COT_STALE")
        self.cot_type = self.config.get("COT_TYPE")
        self.poll_interval: int = int(
            self.config.get("POLL_INTERVAL") or aiscot.DEFAULT_POLL_INTERVAL
        )

        self.include_all_craft = bool(self.config.get("INCLUDE_ALL_CRAFT")) or False

        self.filters = self.config.get("FILTERS")
        self.known_craft = self.config.get("KNOWN_CRAFT")
        self.known_craft_key = self.config.get("KNOWN_CRAFT_KEY") or "MMSI"

        self.filter_type = ""
        self.known_craft_db = None

        self.ais_port = int(self.config.get("AIS_PORT") or aiscot.DEFAULT_AIS_PORT)
        self.listen_host = self.config.get("LISTEN_HOST") or "0.0.0.0"

    async def handle_message(self, msgs) -> None:
        """Handles received MMSI data."""
        # self._logger.info("Received AIS: '%s'", msg)

        for msg in msgs:
            mmsi = str(msg.get("MMSI"))

            known_craft = {}

            if self.filter_type:
                if self.filter_type == "MMSI":
                    filter_key: str = str(mmsi)
                else:
                    filter_key: str = ""

                # self._logger.info("filter_key=%s", filter_key)

                if self.known_craft_db and filter_key:
                    known_craft = (
                        list(
                            filter(
                                lambda x: x[self.known_craft_key].strip().upper()
                                == filter_key,
                                self.known_craft_db,
                            )
                        )
                        or [{}]
                    )[0]
                    # self._logger.debug("known_craft='%s'", known_craft)
                elif filter_key:
                    if "include" in self.filters[
                        self.filter_type
                    ] and filter_key not in self.filters.get(
                        self.filter_type, "include"
                    ):
                        return
                    if "exclude" in self.filters[
                        self.filter_type
                    ] and filter_key in self.filters.get(self.filter_type, "exclude"):
                        return

            # If we're using a known_craft csv and this craft wasn't found, skip:
            if self.known_craft_db and not known_craft and not self.include_all_craft:
                return

            event: str = aiscot.ais_to_cot(
                msg,
                stale=self.cot_stale,
                cot_type=self.cot_type,
                known_craft=known_craft,
            )
            await self._put_event_queue(event)

    async def _get_aishub_feed(self):
        """
        Gets AIS data from AISHub feed.
        """
        feed_url: str = self.aishub_url.geturl()
        self._logger.info("Getting feed from %s", feed_url)

        async with aiohttp.ClientSession() as session:
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
                await self.handle_message(ships)

    async def run(self, number_of_iterations=-1):
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info("Running AISWorker, COT_URL=%s", self.config.get("COT_URL"))
        loop = asyncio.get_event_loop()

        if self.aishub_url:
            if self.known_craft is not None:
                self._logger.info("Using KNOWN_CRAFT File: '%s'", self.known_craft)
                self.known_craft_db = aiscot.read_known_craft(self.known_craft)
                self.filters = configparser.ConfigParser()
                self.filters.add_section(self.known_craft_key)
                self.filters[self.known_craft_key]["include"] = str(
                    [
                        x[self.known_craft_key].strip().upper()
                        for x in self.known_craft_db
                    ]
                )

            if self.filters or self.known_craft_db:
                filter_src = self.filters or self.known_craft_key
                self._logger.debug("filter_src=%s", filter_src)
                if filter_src:
                    if "MMSI" in filter_src:
                        self.filter_type = "MMSI"
                    self._logger.debug("filter_type=%s", self.filter_type)
        else:
            ready = asyncio.Event()
            await loop.create_datagram_endpoint(
                lambda: AISNetworkClient(ready, self.event_queue, self.config),
                local_addr=(self.listen_host, self.ais_port),
            )

            await ready.wait()

        while 1:
            if self.aishub_url:
                await self._get_aishub_feed()
            await asyncio.sleep(self.poll_interval)
