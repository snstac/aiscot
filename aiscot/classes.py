#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Class Definitions."""

import logging
import random
import socket
import threading
import time

import ais.stream

import pycot

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class AISCoT(threading.Thread):

    """AIS Cursor-on-Target Threaded Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aiscot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aiscot.LOG_LEVEL)
        _console_handler.setFormatter(aiscot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, ais_port: int, cot_host: str):
        self.ais_port = ais_port
        self.cot_host = cot_host
        threading.Thread.__init__(self)
        self._stopped = False

    def stop(self):
        """
        Stop the thread at the next opportunity.
        """
        self._stopped = True
        return self._stopped

    def send_cot(self, ais_sentence) -> bool:
        """Sends an AIS Frame to a Cursor-on-Target Host."""
        cot_event = aiscot.ais_to_cot(ais_sentence)
        if cot_event is None:
            return False

        rendered_event = cot_event.render(encoding='UTF-8', standalone=True)

        self._logger.debug(
            'Sending CoT to %s : "%s"', self.cot_host, rendered_event)

        return self.net_client.sendall(rendered_event)

    def run(self):
        """Runs this Thread, reads AIS & outputs CoT."""
        self._logger.info('Running AISCoT Thread...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', int(self.ais_port)))

        self.net_client = pycot.NetworkClient(self.cot_host)

        while 1:
            for msg in ais.stream.decode(sock.makefile('r'), keep_nmea=True):
                self._logger.debug('Received AIS: "%s"', msg)
                self.send_cot(msg)
                time.sleep(random.random())
