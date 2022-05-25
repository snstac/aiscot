#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""AIS Cursor-On-Target Gateway Functions."""

import csv
import datetime
import platform

import xml.etree.ElementTree as ET

import pytak

import aiscot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def ais_to_cot_xml(
    msg: dict, stale: int = None, cot_type: str = "", known_craft: dict = None
) -> ET.Element:
    """
    Converts an AIS Sentence to a Cursor-On-Target Event.

    :param msg: AIS Sentence to convert to COT.
    :type msg: `dict`
    :param cot_stale: Number of Seconds from now to mark the COT Event stale.
    :type cot_stale: `int`
    """
    known_craft = known_craft or {}
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

    point = ET.Element("point")
    point.set("lat", str(msg.get("lat", msg.get("LATITUDE"))))
    point.set("lon", str(msg.get("lon", msg.get("LONGITUDE"))))
    point.set("hae", "9999999.0")
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    contact = ET.Element("contact")
    contact.set("callsign", str(callsign))

    track = ET.Element("track")
    track.set("course", str(msg.get("heading", msg.get("HEADING", 0))))

    # Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    sog = int(msg.get("speed", msg.get("SPEED", 0)))
    if sog:
        track.set("speed", str(sog * 0.514444))
    else:
        track.set("speed", "9999999.0")

    detail = ET.Element("detail")
    detail.set("uid", name)
    detail.append(contact)
    detail.append(track)

    remarks = ET.Element("remarks")

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

    root = ET.Element("event")

    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", name)
    root.set("how", "m-g")
    root.set("time", time.strftime(pytak.ISO_8601_UTC))
    root.set("start", time.strftime(pytak.ISO_8601_UTC))
    root.set(
        "stale",
        (time + datetime.timedelta(seconds=int(cot_stale))).strftime(
            pytak.ISO_8601_UTC
        ),
    )

    root.append(point)
    root.append(detail)

    return root


def ais_to_cot(
    ais_msg: dict, stale: int = None, cot_type: str = "", known_craft: dict = None
) -> str:
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

    return ET.tostring(ais_to_cot_xml(ais_msg, stale, cot_type, known_craft))


def _read_known_craft_fd(csv_fd) -> list:
    """Reads known craft file into an iterable key=value array.

    Parameters
    ----------
    csv_fd : `fd`
        FD Object.

    Returns
    -------
    `list`
        Rows of `dict`s of CSV FD.
    """
    all_rows: list = []
    reader = csv.DictReader(csv_fd)
    for row in reader:
        all_rows.append(row)
    return all_rows


def read_known_craft(csv_file: str) -> list:
    """Reads Known Craft file into an iterable key=value array.

    Parameters
    ----------
    csv_file : `str`
        Path to the Known Craft CSV file.

    Returns
    -------
    `list`
        Rows of `dict`s of Known Crafts.
    """
    all_rows: list = []
    with open(csv_file) as csv_fd:
        all_rows = _read_known_craft_fd(csv_fd)
    return all_rows


def read_mid_db_file(csv_file: str = aiscot.MID_DB_FILE) -> list:
    """Reads the MID_DB_FILE file into a `dict`"""
    mid_digits: list = []
    mid_allocated_to: list = []

    with open(csv_file) as csv_fd:
        reader = csv.DictReader(csv_fd)
        for row in reader:
            mid_digits.append(row["Digit"])
            mid_allocated_to.append(row["Allocated to"])

    return dict(zip(mid_digits, mid_allocated_to))


def read_ship_db_file(csv_file: str = aiscot.SHIP_DB_FILE) -> list:
    """Reads the SHIP_DB_FILE file into a `list`"""
    all_rows: list = []
    fields: list = ["MMSI", "name", "unk", "vtype"]
    with open(csv_file, "r", encoding="ISO-8859-1") as csv_fd:
        reader = csv.DictReader(csv_fd, fields)
        for row in reader:
            all_rows.append(row)
        return all_rows


MID_DB = read_mid_db_file()
SHIP_DB = read_ship_db_file()


def get_mid(mmsi: str) -> str:
    """
    Gets the registered country for a given vessel's MMSI MID.

    Uses the ITU MID Database.

    TK URL to ITU DB.

    Parameters
    ----------
    mmsi : `str`
        MMSI as decoded from AIS data.

    Returns
    -------
    `str`
        Country name in the MID Database from ITU.
    """
    mid: str = str(mmsi)[:3]
    country: str = MID_DB.get(mid)
    return country


def get_aton(mmsi: str) -> bool:
    """
    Gets the AIS Aids-to-Navigation (AtoN) status of a given MMSI.

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
    Gets the AIS Search-And-Rescue (SAR) status of a given MMSI.

    Search and Rescue Aircraft:
        AIS and DSC equipment used on search and rescue aircraft use the format
        111213M4I5D6X7X8X9 where the digits 4, 5 and 6 represent the MID and X
        is any figure from 0 to 9. In the United States, these MMSIs are
        currently only used by the U.S. Coast Guard.
        Src: https://www.navcen.uscg.gov/?pageName=mtmmsi

    :param mmsi: str MMSI as decoded from AIS data.
    :return:
    """
    sar = False
    _mmsi = str(mmsi)
    if _mmsi[:3] == "111":
        sar = True
    elif _mmsi[:5] in ["30386", "33885"]:  # US Coast Guard
        sar = True
    return sar


def get_crs(mmsi: str) -> bool:
    """
    Gets the CRS status of the vessel based on MMSI.

    :param mmsi: MMSI of the vessel.
    :type mmsi: str
    :returns: True if CRS, False otherwise.
    :rtype: bool
    """
    crs = False
    # Known CRS':
    # 3669145
    # 3669708
    # 3669709
    if str(mmsi)[:4] == "3669" and len(str(mmsi)) == 7:
        crs = True
    elif str(mmsi)[:4] == "003369":
        crs = True
    return crs


def get_shipname(mmsi: str) -> str:
    """
    Gets the ship name from the SHIP_DB based on MMSI.

    :param mmsi: MMSI of the ship.
    :returns: Ship name.
    """
    ship_name: str = ""
    for ship in SHIP_DB:
        if str(ship.get("MMSI")) == str(mmsi):
            ship_name = ship.get("name")
    return ship_name
