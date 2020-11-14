#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Class Definitions."""

import asyncio
import io
import logging

import ais.stream
import pytak

import aiscot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2020 Orion Labs, Inc."
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

    def __init__(self, ready, event_queue, cot_stale) -> None:
        self.ready = ready
        self.event_queue = event_queue
        self.cot_stale = cot_stale
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info("peername")
        self._logger.debug('Connection from %s', self.address)
        self.ready.set()

    def datagram_received(self, data, addr):
        self._logger.debug("Recieved from %s: '%s'", addr, data)
        d_data = data.decode()
        for msg in ais.stream.decode(io.StringIO(d_data), keep_nmea=True):
            self._logger.debug("Received AIS: '%s'", msg)

            cot_event = aiscot.ais_to_cot(msg, cot_stale=self.cot_stale)
            if cot_event is None:
                return False
            self.event_queue.put_nowait(cot_event)

    def connection_lost(self, exc):
        self.ready.clear()
        self._logger.exception(exc)
        self._logger.warning("Disconnected from %s", self.address)


class AISWorker(pytak.MessageWorker):

    """AIS Cursor-on-Target Class."""

    def __init__(self, event_queue, cot_stale: int,
                 ais_port: int = None) -> None:
        super().__init__(event_queue, cot_stale)
        self.ais_port = ais_port or aiscot.DEFAULT_AIS_PORT

    async def run(self):
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info("Running AISWorker")
        loop = asyncio.get_event_loop()

        ready = asyncio.Event()
        trans, proto = await loop.create_datagram_endpoint(
            lambda: AISNetworkClient(ready, self.event_queue, self.cot_stale),
            local_addr=('0.0.0.0', int(self.ais_port))
        )

        await ready.wait()
        while 1:
            await asyncio.sleep(0.01)
