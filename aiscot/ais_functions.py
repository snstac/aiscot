#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# AISCOT ais_functions.py
#
# Copyright Sensors & Signals LLC https://www.snstac.com
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

"""AISCOT Functions."""

from csv import DictReader
from typing import TextIO

import aiscot

__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright 2023 Sensors & Signals LLC"
__license__ = "Apache License, Version 2.0"


def read_known_craft_fd(csv_fd: TextIO) -> list:
    """Split a CSV file into an iterable key=value store.

    Parameters
    ----------
    csv_fd : The File discriptor of the opened Known Craft file.

    Returns
    -------
    All Known Craft transforms.
    """
    all_rows: list = []
    reader = DictReader(csv_fd)
    for row in reader:
        all_rows.append(row)
    return all_rows


def get_known_craft(csv_file: str) -> list:
    """Read an AISCOT Known Craft file into an iterable list of transforms.

    Parameters
    ----------
    csv_file : The path to the Known Craft file.

    Returns
    -------
    All Known Craft transforms.
    """
    all_rows: list = []
    with open(csv_file, encoding="UTF-8") as csv_fd:
        all_rows = read_known_craft_fd(csv_fd)
    return all_rows


def read_mid_db_file(csv_file: str = "") -> dict:
    """Read the MID_DB_FILE file into a `dict`."""
    csv_file = csv_file or aiscot.DEFAULT_MID_DB_FILE
    mid_digits: list = []
    mid_allocated_to: list = []

    with open(csv_file, encoding="UTF-8") as csv_fd:
        reader = DictReader(csv_fd)
        for row in reader:
            mid_digits.append(row["Digit"])
            mid_allocated_to.append(row["Allocated to"])

    return dict(zip(mid_digits, mid_allocated_to))


def read_ship_db_file(csv_file: str = "") -> list:
    """Read the SHIP_DB_FILE file into a `list`."""
    csv_file = csv_file or aiscot.DEFAULT_SHIP_DB_FILE
    all_rows: list = []
    fields: list = ["MMSI", "name", "unk", "vtype"]
    with open(csv_file, "r", encoding="ISO-8859-1") as csv_fd:
        reader = DictReader(csv_fd, fields)
        for row in reader:
            all_rows.append(row)
        return all_rows


MID_DB = read_mid_db_file()
SHIP_DB = read_ship_db_file()


def get_mid(mmsi: str) -> str:
    """Get the registered country for a given vessel's MMSI MID.

    Uses the ITU MID Database.

    TK URL to ITU DB.

    Parameters
    ----------
    mmsi : MMSI as decoded from AIS data.

    Returns
    -------
    Country name in the MID Database from ITU.
    """
    mid: str = str(mmsi)[:3]
    country: str = MID_DB.get(mid)
    return country


def get_aton(mmsi: str) -> bool:
    """Get the AIS Aids-to-Navigation (AtoN) status of a given MMSI.

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
    """Get the AIS Search-And-Rescue (SAR) status of a given MMSI.

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
    """Get the CRS status of the vessel based on MMSI.

    :param mmsi: MMSI of the vessel.
    :type mmsi: str
    :returns: True if CRS, False otherwise.
    :rtype: bool
    """
    crs = False
    # Known CRS:
    # 3669145
    # 3669708
    # 3669709
    if str(mmsi)[:4] == "3669" and len(str(mmsi)) == 7:
        crs = True
    elif str(mmsi)[:6] == "003369":
        crs = True
    return crs


def get_shipname(mmsi: str) -> str:
    """Get the ship name from the Ship DB based on the MMSI.

    :param mmsi: MMSI of the ship.
    :returns: Ship name.
    """
    ship_name: str = ""
    # TODO: Optimize this search:
    for ship in SHIP_DB:
        if str(ship.get("MMSI")) == str(mmsi):
            ship_name = ship.get("name")
            break
    return ship_name
