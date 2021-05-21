#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Class Definitions."""

import asyncio
import configparser
import io
import logging

import pytak

import aiscot

import aiscot.pyAISm

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2021 Orion Labs, Inc."
__license__ = "Apache License, Version 2.0"


class AISNetworkClient(asyncio.Protocol):

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
        d_data = data.decode().strip()
        msg = aiscot.pyAISm.decod_ais(d_data)

        # self._logger.debug("Received AIS: '%s'", msg)

        mmsi = str(msg.get("mmsi"))

        known_craft = {}

        if self.filter_type:
            if self.filter_type == "MMSI":
                filter_key: str = mmsi
            else:
                filter_key: str = ""

            # self._logger.debug("filter_key=%s", filter_key)

            if self.known_craft_db and filter_key:
                known_craft = (list(filter(
                    lambda x: x[self.known_craft_key].strip().upper() == filter_key, self.known_craft_db)) or
                               [{}])[0]
                # self._logger.debug("known_craft='%s'", known_craft)
            elif filter_key:
                if "include" in self.filters[self.filter_type] and filter_key not in self.filters.get(filter_type,
                                                                                                 "include"):
                    return
                if "exclude" in self.filters[self.filter_type] and filter_key in self.filters.get(filter_type,
                                                                                             "exclude"):
                    return

        # If we're using a known_craft csv and this craft wasn't found, skip:
        if self.known_craft_db and not known_craft and not self.include_all_craft:
            return

        event: str = aiscot.ais_to_cot(msg, stale=self.cot_stale, cot_type=self.cot_type, known_craft=known_craft)

        if event:
            self.event_queue.put_nowait(event)

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info("peername")
        self._logger.debug("Connection from %s", self.address)

        if self.known_craft is not None:
            self._logger.info("Using KNOWN_CRAFT File: '%s'", self.known_craft)
            self.known_craft_db = aiscot.read_known_craft(self.known_craft)
            self.filters = configparser.ConfigParser()
            self.filters.add_section(self.known_craft_key)
            self.filters[self.known_craft_key]["include"] = \
                str([x[self.known_craft_key].strip().upper() for x in self.known_craft_db])

        if self.filters or self.known_craft_db:
            filter_src = self.filters or self.known_craft_key
            self._logger.debug("filter_src=%s", filter_src)
            if filter_src:
                if "MMSI" in filter_src:
                    self.filter_type = "MMSI"
                self._logger.debug("filter_type=%s", self.filter_type)

        self.ready.set()

    def datagram_received(self, data, addr):
        self._logger.debug("Recieved from %s: '%s'", addr, data)
        for line in data.splitlines():
            self.handle_message(line)

    def connection_lost(self, exc):
        self.ready.clear()
        self._logger.exception(exc)
        self._logger.warning("Disconnected from %s", self.address)


class AISWorker(pytak.MessageWorker):

    """AIS Cursor-on-Target Class."""

    def __init__(self, event_queue, opts) -> None:
        super().__init__(event_queue)
        self.opts = opts
        self.ais_port = int(opts.get("AIS_PORT") or aiscot.DEFAULT_AIS_PORT)
        self.listen_host = opts.get("LISTEN_HOST") or "0.0.0.0"

    async def run(self):
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info("Running AISWorker")
        loop = asyncio.get_event_loop()

        ready = asyncio.Event()
        trans, proto = await loop.create_datagram_endpoint(
            lambda: AISNetworkClient(ready, self.event_queue, self.opts),
            local_addr=(self.listen_host, self.ais_port)
        )

        await ready.wait()
        while 1:
            await asyncio.sleep(0.01)
