#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Functions."""

import datetime

import pycot

import aiscot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def ais_to_cot(ais_sentence: dict, cot_stale: int = None) -> pycot.Event:
    """
    Converts an AIS Sentence to a Cursor-on-Target Event.

    :param ais_sentence: AIS Sentence to convert to CoT.
    :type ais_sentence: `dict`
    """
    time = datetime.datetime.now(datetime.timezone.utc)
    cot_stale = cot_stale or aiscot.DEFAULT_STALE
    cot_type = aiscot.DEFAULT_TYPE

    lat = ais_sentence.get("y")
    lon = ais_sentence.get("x")
    mmsi = ais_sentence.get("mmsi")

    if lat is None or lon is None or mmsi is None:
        return None

    name = f"MMSI-{mmsi}"
    _name = ais_sentence.get("name", "").replace("@", "").strip()
    if _name:
        callsign = _name
    else:
        callsign = mmsi

    point = pycot.Point()
    point.lat = lat
    point.lon = lon
    point.ce = "9999999.0"
    point.le = "9999999.0"
    point.hae = "9999999.0"

    uid = pycot.UID()
    uid.Droid = name

    contact = pycot.Contact()
    contact.callsign = callsign
    # Not supported by FTS 1.1 yet?
    # contact.hostname = f'https://www.marinetraffic.com/en/ais/details/ships/mmsi:{mmsi}'

    track = pycot.Track()
    track.course = ais_sentence.get("true_heading", 0)

    # Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    sog = int(ais_sentence.get("sog", 0))
    if sog:
        track.speed = sog * 0.514444
    else:
        track.speed = "9999999.0"

    remarks = pycot.Remarks()
    _remark = f"MMSI: {mmsi}"
    if _name:
        remarks.value = f"Name: {_name} " + _remark
    else:
        remarks.value = _remark

    detail = pycot.Detail()
    detail.uid = uid
    detail.contact = contact
    detail.track = track
    # Not supported by FTS 1.1 yet?
    # detail.remarks = remarks

    event = pycot.Event()
    event.version = "2.0"
    event.event_type = cot_type
    event.uid = name
    event.time = time
    event.start = time
    event.stale = time + datetime.timedelta(seconds=cot_stale)  # 1 hour expire
    event.how = "m-g"
    event.point = point
    event.detail = detail

    return event


def hello_event():
    time = datetime.datetime.now(datetime.timezone.utc)
    name = 'aiscot'
    callsign = 'aiscot'

    point = pycot.Point()
    point.lat = 0.0
    point.lon = 0.0

    # FIXME: These values are static, should be dynamic.
    point.ce = '9999999.0'
    point.le = '9999999.0'
    point.hae = '9999999.0'

    uid = pycot.UID()
    uid.Droid = name

    contact = pycot.Contact()
    contact.callsign = callsign

    detail = pycot.Detail()
    detail.uid = uid
    detail.contact = contact

    event = pycot.Event()
    event.version = '2.0'
    event.event_type = 'a-u-G'
    event.uid = name
    event.time = time
    event.start = time
    event.stale = time + datetime.timedelta(hours=1)
    event.how = 'h-g-i-g-o'
    event.point = point
    event.detail = detail

    return event
