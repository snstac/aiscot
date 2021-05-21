#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Functions."""

import csv
import datetime
import platform

import xml.etree.ElementTree

import pytak

import aiscot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2021 Orion Labs, Inc."
__license__ = "Apache License, Version 2.0"



def ais_to_cot_xml(ais_msg: dict, stale: int = None, cot_type: str = "",
                   known_craft: dict = {}) -> xml.etree.ElementTree.Element:
    """
    Converts an AIS Sentence to a Cursor-on-Target Event.

    :param ais_msg: AIS Sentence to convert to CoT.
    :type ais_msg: `dict`
    :param cot_stale: Number of Seconds from now to mark the CoT Event stale.
    :type cot_stale: `int`
    """
    time = datetime.datetime.now(datetime.timezone.utc)

    cot_stale = stale or known_craft.get("STALE") or aiscot.DEFAULT_COT_STALE
    cot_type = known_craft.get("COT") or cot_type or aiscot.DEFAULT_COT_TYPE

    mmsi = ais_msg.get("mmsi")
    ais_name = ais_msg.get("name", "").replace("@", "").strip()

    name = f"MMSI-{mmsi}"
    _name = known_craft.get("NAME") or ais_name
    if _name:
        callsign = _name
    else:
        callsign = mmsi

    point = xml.etree.ElementTree.Element("point")
    point.set("lat", str(ais_msg.get("lat")))
    point.set("lon", str(ais_msg.get("lon")))
    point.set("hae", "9999999.0")
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    uid = xml.etree.ElementTree.Element("UID")
    uid.set("Droid", str(callsign))

    contact = xml.etree.ElementTree.Element("contact")
    contact.set("callsign", str(callsign))

    track = xml.etree.ElementTree.Element("track")
    track.set("course", str(ais_msg.get("heading", 0)))

    # Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    sog = int(ais_msg.get("speed", 0))
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
    if ais_name:
        _remark = f"AIS Name: {ais_name} {_remark} (via aiscot@{platform.node()})"
        detail.set("remarks", _remark)
        remarks.text = _remark
    else:
        _remark = f"{_remark} (via aiscot@{platform.node()})"
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

    return root


def ais_to_cot(ais_msg: dict, stale: int = None, cot_type: str = "", known_craft: dict = {}) -> str:
    """
    Converts an AIS Sentence to a Cursor-on-Target Event as a Python `str` String.

    See `ais_to_cot_xml()` for XML Object output version of this function.

    :param ais_msg: AIS Sentence to convert to CoT.
    :type ais_msg: `dict`
    :param cot_stale: Number of Seconds from now to mark the CoT Event stale.
    :type cot_stale: `int`
    """
    lat = ais_msg.get("lat")
    lon = ais_msg.get("lon")
    mmsi = ais_msg.get("mmsi")

    if lat is None or lon is None or mmsi is None:
        return None

    return xml.etree.ElementTree.tostring(ais_to_cot_xml(ais_msg, stale, cot_type, known_craft))


def read_known_craft(csv_file: str) -> list:
    """Reads the FILTER_CSV file into a `list`"""
    all_rows = []
    with open(csv_file) as csv_fd:
        reader = csv.DictReader(csv_fd)
        for row in reader:
            all_rows.append(row)
    return all_rows
