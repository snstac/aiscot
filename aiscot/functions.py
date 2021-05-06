#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Functions."""

import datetime

import xml.etree.ElementTree

import pytak

import aiscot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2021 Orion Labs, Inc."
__license__ = "Apache License, Version 2.0"


def ais_to_cot(ais_sentence: dict, cot_stale: int = None) -> str:
    """
    Converts an AIS Sentence to a Cursor-on-Target Event.

    :param ais_sentence: AIS Sentence to convert to CoT.
    :type ais_sentence: `dict`
    :param cot_stale: Number of Seconds from now to mark the CoT Event stale.
    :type cot_stale: `int`
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

    point = xml.etree.ElementTree.Element("point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", "9999999.0")
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    uid = xml.etree.ElementTree.Element("UID")
    uid.set("Droid", name)

    contact = xml.etree.ElementTree.Element("contact")
    contact.set("callsign", str(callsign))

    track = xml.etree.ElementTree.Element("track")
    track.set("course", str(ais_sentence.get("true_heading", 0)))

    # Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    sog = int(ais_sentence.get("sog", 0))
    if sog:
        track.set("speed", str(sog * 0.514444))
    else:
        track.set("speed", "9999999.0")

    detail = xml.etree.ElementTree.Element("detail")
    detail.set("uid", name)
    detail.append(uid)
    detail.append(contact)
    detail.append(track)

    remarks = xml.etree.ElementTree.Element("remarks")
    _remark = f"MMSI: {mmsi}"
    if _name:
        _remark = f"Name: {_name} {_remark}"
        detail.set("remarks", _remark)
        remarks.text = _remark
    else:
        detail.set("remarks", _remark)
        remarks.text = _remark

    detail.append(remarks)

    root = xml.etree.ElementTree.Element("event")
    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", name)
    root.set("how", "m-g")
    root.set("time", time.strftime(pytak.ISO_8601_UTC))
    root.set("start", time.strftime(pytak.ISO_8601_UTC))
    root.set("stale", (time + datetime.timedelta(seconds=int(cot_stale))).strftime(pytak.ISO_8601_UTC))
    root.append(point)
    root.append(detail)

    return xml.etree.ElementTree.tostring(root)
