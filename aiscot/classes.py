#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Class Definitions."""

import asyncio
import io
import logging
import queue
import socket

import ais.stream

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class AISWorker:

    """AIS Cursor-on-Target Threaded Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aiscot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aiscot.LOG_LEVEL)
        _console_handler.setFormatter(aiscot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, msg_queue, ais_port: int = None,
                 stale: int = None):
        self.msg_queue = msg_queue
        self.ais_port = ais_port or aiscot.DEFAULT_AIS_PORT
        self.stale = stale or aiscot.DEFAULT_STALE

    async def run(self):
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info('Running AISWorker')
        loop = asyncio.get_event_loop()

        await self.msg_queue.put(
            aiscot.hello_event().render(encoding='UTF-8', standalone=True))

        ready = asyncio.Event()
        trans, proto = await loop.create_datagram_endpoint(
            lambda: AISNetworkClient(self.msg_queue, ready, self.stale),
            local_addr=('0.0.0.0', int(self.ais_port))
        )

        await ready.wait()


class AISNetworkClient(asyncio.Protocol):

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aiscot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aiscot.LOG_LEVEL)
        _console_handler.setFormatter(aiscot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger('asyncio').setLevel(aiscot.LOG_LEVEL)

    def __init__(self, msg_queue, ready, stale) -> None:
        self.msg_queue = msg_queue
        self.ready = ready
        self.stale = stale

        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self._logger.debug('Connected to %s', self.address)
        self.ready.set()

    def datagram_received(self, data, addr):
        # self._logger.debug('Received "%s"', data.decode())
        d_data = data.decode()
        for msg in ais.stream.decode(io.StringIO(d_data), keep_nmea=True):
            self._logger.debug('Received AIS: "%s"', msg)

            cot_event = aiscot.ais_to_cot(msg, stale=self.stale)
            if cot_event is None:
                return False

            rendered_event = cot_event.render(encoding='UTF-8', standalone=True)

            if rendered_event:
                self.msg_queue.put_nowait(rendered_event)

    def connection_lost(self, exc):
        self.ready.clear()
        self._logger.warning('Disconnected from %s', self.address)
        self._logger.exception(exc)
