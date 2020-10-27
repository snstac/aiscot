#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Class Definitions."""

import logging
import queue
import socket
import threading

import ais.stream

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class AISWorker(threading.Thread):

    """AIS Cursor-on-Target Threaded Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aiscot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aiscot.LOG_LEVEL)
        _console_handler.setFormatter(aiscot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, msg_queue: queue.Queue, ais_port: int = None,
                 stale: int = None):
        self.msg_queue = msg_queue
        self.ais_port = ais_port or aiscot.DEFAULT_AIS_PORT
        self.stale = stale or aiscot.DEFAULT_STALE_PERIOD

        # Thread setup:
        threading.Thread.__init__(self)
        self.daemon = True
        self._stopper = threading.Event()

    def stop(self):
        """Stop the thread at the next opportunity."""
        self._logger.debug('Stopping AISWorker')
        self._stopper.set()

    def stopped(self):
        """Checks if the thread is stopped."""
        return self._stopper.isSet()

    def _put_queue(self, msg: dict) -> None:
        cot_event = aiscot.ais_to_cot(msg)
        if cot_event is None:
            return False

        rendered_event = cot_event.render(encoding='UTF-8', standalone=True)

        if rendered_event:
            try:
                self.msg_queue.put(rendered_event, True, 10)
            except queue.Full as exc:
                self._logger.exception(exc)
                self._logger.warning(
                    'Lost CoT Event (queue full): "%s"', rendered_event)

    def _receive_ais(self):
        for msg in ais.stream.decode(self.sock.makefile('r'), keep_nmea=True):
            self._logger.debug('Received AIS: "%s"', msg)
            self._put_queue(msg)

    def run(self):
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info('Running AISWorker')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', int(self.ais_port)))

        while not self.stopped():
            self._receive_ais()
