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
__copyright__ = "Copyright 2021 Greg Albrecht, Inc."
__license__ = "Apache License, Version 2.0"


def ais_to_cot_xml(msg: dict, stale: int = None, cot_type: str = "",
                   known_craft: dict = {}) -> xml.etree.ElementTree.Element:
    """
    Converts an AIS Sentence to a Cursor-on-Target Event.

    :param msg: AIS Sentence to convert to CoT.
    :type msg: `dict`
    :param cot_stale: Number of Seconds from now to mark the CoT Event stale.
    :type cot_stale: `int`
    """
    time = datetime.datetime.now(datetime.timezone.utc)

    cot_stale = stale or known_craft.get("STALE") or aiscot.DEFAULT_COT_STALE

    mmsi = msg.get("mmsi", msg.get("MMSI"))

    ais_name: str = msg.get("name", msg.get("NAME", "")).replace("@", "").strip()
    shipname: str = msg.get("shipname", aiscot.get_shipname(mmsi))

    if shipname:
        ais_name = shipname

    name = f"MMSI-{mmsi}"
    _name = known_craft.get("NAME") or ais_name
    if _name:
        callsign = _name
    else:
        callsign = mmsi

    if known_craft.get("NAME"):
        print(f"NAME = {_name} MMSI = {mmsi}")

    cot_type = known_craft.get("COT") or cot_type or aiscot.DEFAULT_COT_TYPE

    country: str = aiscot.get_mid(mmsi)
    if country and "United States of America" in country:
        cot_type = "a-f" + cot_type[3:]
    elif country:
        cot_type = "a-n" + cot_type[3:]

    aton: bool = aiscot.get_aton(mmsi)
    if aton:
        cot_type = "a-n-S-N"
        cot_stale = 86400  # 1 Day
        callsign = f"AtoN {callsign}"

    uscg: bool = aiscot.get_sar(mmsi)
    if uscg:
        cot_type = "a-f-S-X-L"

    crs: bool = aiscot.get_crs(mmsi)
    if crs:
        cot_type = "a-f-G-I-U-T"
        cot_stale = 86400  # 1 Day
        callsign = f"USCG CRS {callsign}"

    point = xml.etree.ElementTree.Element("point")
    point.set("lat", str(msg.get("lat", msg.get("LATITUDE"))))
    point.set("lon", str(msg.get("lon", msg.get("LONGITUDE"))))
    point.set("hae", "9999999.0")
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    contact = xml.etree.ElementTree.Element("contact")
    contact.set("callsign", str(callsign))

    track = xml.etree.ElementTree.Element("track")
    track.set("course", str(msg.get("heading", msg.get("HEADING",0))))

    # Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    sog = int(msg.get("speed", msg.get("SPEED", 0)))
    if sog:
        track.set("speed", str(sog * 0.514444))
    else:
        track.set("speed", "9999999.0")

    detail = xml.etree.ElementTree.Element("detail")
    detail.set("uid", name)
    detail.append(contact)
    detail.append(track)

    remarks = xml.etree.ElementTree.Element("remarks")

    if crs:
        remark = f"USCG CRS {mmsi}"
        if ais_name:
            remark = f"USCG CRS {ais_name} {mmsi}"
    else:
        _remark = f"AtoN/{aton} MMSI/{mmsi} Co/{country}"
        if ais_name:
            remark = f"{ais_name} {_remark}"
        else:
            remark = _remark

    _remarks = f"{remark} Ty/{msg.get('type', msg.get('TYPE'))} Sn/{shipname}"
    remarks.text = f"{_remarks} aiscot@{platform.node()}"
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
    all_rows: list = []
    with open(csv_file) as csv_fd:
        reader = csv.DictReader(csv_fd)
        for row in reader:
            all_rows.append(row)
    return all_rows


## NEW

MID_DIGITS = []
MID_ALLOCATED_TO = []

def read_mid_db_file(csv_file: str) -> list:
    """Reads the MID_DB_FILE file into a `list`"""
    with open(csv_file) as csv_fd:

        reader = csv.DictReader(csv_fd)
        for row in reader:
            MID_DIGITS.append(row["Digit"])
            MID_ALLOCATED_TO.append(row["Allocated to"])

        return reader


MID_DB_FILE = "MaritimeIdentificationDigits-bb62983a-cf0e-40a1-9431-cd54eaeb1c85.csv"
read_mid_db_file(MID_DB_FILE)

MID_DB = dict(zip(MID_DIGITS, MID_ALLOCATED_TO))

def get_mid(mmsi: str) -> str:
    """
    Gets the country for a given MMSI's MID.
    :param mmsi: str MMSI as decoded from AIS data.
    :return: str Country name in the MID Database from ITU.
    """
    mid: str = str(mmsi)[:3]
    country: str = MID_DB.get(mid)
    if country:
        return country


def get_aton(mmsi: str) -> bool:
    """
    Gets the AIS Aids to Navigation (AtoN) status of a given MMSI.

    AIS Aids to Navigation (AtoN):
        AIS used as an aid to navigation uses the format 9192M3I4D5X6X7X8X9
        where the digits 3, 4 and 5 represent the MID and X is any figure
        from 0 to 9. In the United States, these MMSIs are reserved for the
        federal government.
        Src: https://www.navcen.uscg.gov/?pageName=mtmmsi

    :param mmsi: str MMSI as decoded from AIS data.
    :return: bool True if MMSI belongs to an AtoN, otherwise False.
    """
    return str(mmsi)[:2] == "99"


def get_sar(mmsi: str) -> bool:
    """
    Search and Rescue Aircraft:
        AIS and DSC equipment used on search and rescue aircraft use the format
        111213M4I5D6X7X8X9 where the digits 4, 5 and 6 represent the MID and X
        is any figure from 0 to 9. In the United States, these MMSIs are
        currently only used by the U.S. Coast Guard.
        Src: https://www.navcen.uscg.gov/?pageName=mtmmsi

    :param mmsi: str MMSI as decoded from AIS data.
    :return:
    """
    _mmsi = str(mmsi)
    if _mmsi[:3] == "111":
        return True
    elif _mmsi[:5] in ["30386", "33885"]:  # US Coast Guard
        return True


def get_crs(mmsi: str) -> bool:
    # 3669145
    # 3669708
    # 3669709
    if str(mmsi)[:4] == "3669" and len(str(mmsi)) == 7:
        return True
    elif str(mmsi)[:4] == "003369":
        return True
    else:
        return False


def read_ship_db_file(csv_file: str) -> list:
    """Reads the MID_DB_FILE file into a `list`"""
    all_rows: list = []
    fields: list = ["MMSI", "name", "unk", "vtype"]
    with open(csv_file, 'r', encoding='ISO-8859-1') as csv_fd:
        reader = csv.DictReader(csv_fd, fields)
        for row in reader:
            all_rows.append(row)
        return all_rows


SHIP_DB_FILE = "yadd_mmsi_ship_2021-11-03-170131.txt"
SHIP_DB = read_ship_db_file(SHIP_DB_FILE)


def get_shipname(mmsi: str) -> str:
    for ship in SHIP_DB:
        if str(ship.get("MMSI")) == str(mmsi):
            return ship.get("name")
