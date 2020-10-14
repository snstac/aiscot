#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Functions."""

import datetime

import pycot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def ais_to_cot(ais_sentence: dict) -> pycot.Event:
    """
    Converts an AIS Sentence to a Cursor-on-Target Event.

    :param ais_sentence: AIS Sentence to convert to CoT.
    :type ais_sentence: `dict`
    """
    time = datetime.datetime.now(datetime.timezone.utc)

    lat = ais_sentence.get('y')
    lon = ais_sentence.get('x')
    mmsi = ais_sentence.get('mmsi')

    if lat is None or lon is None or mmsi is None:
        return None

    point = pycot.Point()
    point.lat = lat
    point.lon = lon
    point.ce = '10'
    point.le = '10'
    point.hae = '10'

    uid = pycot.UID()
    uid.Droid = ais_sentence.get('name', mmsi)

    detail = pycot.Detail()
    detail.uid = uid

    event = pycot.Event()
    event.version = '2.0'
    event.event_type = 'a-f-G-E-V-C'
    event.uid = f"AIS.{mmsi}"
    event.time = time
    event.start = time
    event.stale = time + + datetime.timedelta(hours=1)  # 1 hour expire
    event.how = 'h-e'
    event.point = point
    event.detail = detail

    return event
