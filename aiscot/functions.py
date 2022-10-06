#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Greg Albrecht <oss@undef.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author:: Greg Albrecht W2GMD <oss@undef.net>
#

"""AISCOT Functions."""

import csv
import configparser
import xml.etree.ElementTree as ET

from typing import Union

import pytak
import aiscot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


def create_tasks(
    config: Union[dict, configparser.ConfigParser], clitool: pytak.CLITool
) -> set:
    """
    Creates specific coroutine task set for this application.

    Parameters
    ----------
    config : `dict`, `configparser.ConfigParser`
        A `dict` of configuration parameters & values.
    clitool : `pytak.CLITool`
        A PyTAK Worker class instance.

    Returns
    -------
    `set`
        Set of PyTAK Worker classes for this application.
    """
    return set([aiscot.AISWorker(clitool.tx_queue, config)])


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def ais_to_cot_xml(
    craft: dict, config: Union[dict, None] = None, known_craft: Union[dict, None] = None
) -> ET.Element:
    """
    Converts an AIS Sentence to a Cursor-On-Target Event.

    Parameters
    ----------
    msg : `dict`
        AIS sentence serialized as a `dict`.
    clitool : `pytak.CLITool`
        A PyTAK Worker class instance.

    Returns
    -------
    `xml.etree.ElementTree.Element`
        Cursor-On-Target XML ElementTree object.
    """
    lat = craft.get("lat", craft.get("LATITUDE"))
    lon = craft.get("lon", craft.get("LONGITUDE"))
    mmsi = craft.get("mmsi", craft.get("MMSI"))

    if lat is None or lon is None or mmsi is None:
        return None

    known_craft = known_craft or {}
    remarks_fields = []
    config: dict = config or {}

    cot_stale = (
        config.get("COT_STALE", None)
        or known_craft.get("STALE")
        or aiscot.DEFAULT_COT_STALE
    )
    cot_type = (
        config.get("COT_TYPE", None)
        or known_craft.get("COT")
        or aiscot.DEFAULT_COT_TYPE
    )
    cot_host_id = config.get("COT_HOST_ID")

    aiscotx = ET.Element("_aiscot_")
    aiscotx.set("cot_host_id", cot_host_id)

    ais_name: str = craft.get("name", craft.get("NAME", "")).replace("@", "").strip()
    shipname: str = craft.get("shipname", aiscot.get_shipname(mmsi))
    vessel_type: str = craft.get("type", craft.get("TYPE"))

    if ais_name:
        remarks_fields.append(f"AIS Name: {ais_name}")
        aiscotx.set("ais_name", ais_name)

    if shipname:
        ais_name = shipname
        remarks_fields.append(f"Shipname: {shipname}")
        aiscotx.set("shipname", shipname)

    uid = f"MMSI-{mmsi}"

    _name = known_craft.get("NAME") or ais_name
    if _name:
        callsign = _name
    else:
        callsign = mmsi

    country: str = aiscot.get_mid(mmsi)
    if country:
        cot_type = "a-n" + cot_type[3:]
        remarks_fields.append(f"Country: {country}")
        aiscotx.set("country", country)
        if "United States of America" in country:
            cot_type = "a-f" + cot_type[3:]

    if vessel_type:
        ais_name = shipname
        remarks_fields.append(f"Type: {vessel_type}")
        aiscotx.set("type", str(vessel_type))

    if mmsi:
        remarks_fields.append(f"MMSI: {mmsi}")
        aiscotx.set("mmsi", str(mmsi))

    aton: bool = aiscot.get_aton(mmsi)
    aiscotx.set("aton", str(aton))
    if aton:
        cot_type = "a-n-S-N"
        cot_stale = 86400  # 1 Day
        callsign = f"AtoN {callsign}"
        remarks_fields.append(f"AtoN: {aton}")

    uscg: bool = aiscot.get_sar(mmsi)
    aiscotx.set("uscg", str(uscg))
    if uscg:
        cot_type = "a-f-S-X-L"
        remarks_fields.append(f"USCG: {uscg}")

    crs: bool = aiscot.get_crs(mmsi)
    aiscotx.set("crs", str(crs))
    if crs:
        cot_type = "a-f-G-I-U-T"
        cot_stale = 86400  # 1 Day
        callsign = f"USCG CRS {callsign}"
        remarks_fields.append(f"USCG CRS: {crs}")

    # Point
    point = ET.Element("point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", "9999999.0")
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    # Track
    track = ET.Element("track")
    heading: float = craft.get("heading", craft.get("HEADING", 0))  # * 0.1
    track.set("course", str(heading))

    # AIS Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    # COT Speed is meters/second
    sog: float = craft.get("speed", craft.get("SPEED", 0)) * 0.1 / 1.944
    if sog != 0.0:
        speed = str(sog)
    else:
        speed = "9999999.0"
    track.set("speed", speed)

    # Contact
    contact = ET.Element("contact")
    contact.set("callsign", str(callsign))

    remarks = ET.Element("remarks")
    remarks_fields.append(f"{cot_host_id}")
    _remarks = " ".join(list(filter(None, remarks_fields)))
    remarks.text = _remarks

    detail = ET.Element("detail")
    detail.set("uid", uid)
    detail.append(track)
    detail.append(contact)
    detail.append(remarks)

    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", uid)
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(cot_stale))

    root.append(point)
    root.append(detail)
    root.append(aiscotx)

    return root


def ais_to_cot(
    craft: dict, config: Union[dict, None] = None, known_craft: Union[dict, None] = None
) -> bytes:
    """Wrapper for `ais_to_cot_xml` that returns COT as an XML string."""
    cot: ET.ElementTree = ais_to_cot_xml(craft, config, known_craft)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)]) if cot else None
    )

def _read_known_craft_fd(csv_fd) -> list:
    """Reads known craft file into an iterable key=value array.

    Parameters
    ----------
    csv_fd : fd
        FD Object.

    Returns
    -------
    list
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


def read_mid_db_file(csv_file: str = aiscot.DEFAULT_MID_DB_FILE) -> list:
    """Reads the MID_DB_FILE file into a `dict`"""
    mid_digits: list = []
    mid_allocated_to: list = []

    with open(csv_file) as csv_fd:
        reader = csv.DictReader(csv_fd)
        for row in reader:
            mid_digits.append(row["Digit"])
            mid_allocated_to.append(row["Allocated to"])

    return dict(zip(mid_digits, mid_allocated_to))


def read_ship_db_file(csv_file: str = aiscot.DEFAULT_SHIP_DB_FILE) -> list:
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
