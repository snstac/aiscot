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

import logging
import os

from csv import DictReader
from typing import TextIO

import aiscot

Logger = logging.getLogger(__name__)
Debug = bool(os.getenv("DEBUG", False))


def read_known_craft_fd(csv_fd: TextIO) -> list:
    """Split a CSV file into an iterable key=value store.

    Parameters
    ----------
    csv_fd : The File discriptor of the opened Known Craft file.

    Returns
    -------
    All Known Craft transforms.
    """
    return list(DictReader(csv_fd))


def get_known_craft(csv_file: str) -> list:
    """Read an AISCOT Known Craft file into an iterable list of transforms.

    Parameters
    ----------
    csv_file : The path to the Known Craft file.

    Returns
    -------
    All Known Craft transforms.
    """
    if Debug:
        Logger.debug(f"Reading Known Craft file: {csv_file}")
    with open(csv_file, encoding="UTF-8") as csv_fd:
        return read_known_craft_fd(csv_fd)


def read_mid_db_file(csv_file: str = "") -> dict:
    """Read the MID_DB_FILE file into a `dict`."""
    csv_file = csv_file or aiscot.DEFAULT_MID_DB_FILE
    if Debug:
        Logger.debug(f"Reading MID DB file: {csv_file}")

    with open(csv_file, encoding="UTF-8") as csv_fd:
        reader = DictReader(csv_fd)
        return {row["Digit"]: row["Allocated to"] for row in reader}


def read_ship_db_file(csv_file: str = "") -> list:
    """Read the SHIP_DB_FILE file into a `list`."""
    csv_file = csv_file or aiscot.DEFAULT_SHIP_DB_FILE
    if Debug:
        Logger.debug(f"Reading Ship DB file: {csv_file}")

    fields: list = ["MMSI", "name", "unk", "vtype"]

    with open(csv_file, "r", encoding="ISO-8859-1") as csv_fd:
        return list(DictReader(csv_fd, fields))


_mid_db_cache: dict = {}
_ship_db_cache: list = []


def get_mid_db() -> dict:
    """Get MID database, loading it only once (lazy initialization)."""
    global _mid_db_cache
    if not _mid_db_cache:
        _mid_db_cache = read_mid_db_file()
    return _mid_db_cache


def get_ship_db() -> list:
    """Get ship database, loading it only once (lazy initialization)."""
    global _ship_db_cache
    if not _ship_db_cache:
        _ship_db_cache = read_ship_db_file()
    return _ship_db_cache


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
    mmsi = str(mmsi)
    mid_db = get_mid_db()
    return mid_db.get(mmsi[:3], "")


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
    mmsi = str(mmsi)
    return mmsi[:2] == "99"


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
    mmsi = str(mmsi)
    if mmsi[:3] == "111":
        return True
    return mmsi[:5] in ("30386", "33885")  # US Coast Guard


def get_crs(mmsi: str) -> bool:
    """Get the CRS status of the vessel based on MMSI.

    :param mmsi: MMSI of the vessel.
    :type mmsi: str
    :returns: True if CRS, False otherwise.
    :rtype: bool
    """
    mmsi = str(mmsi)
    # Known CRS:
    # 3669145
    # 3669708
    # 3669709
    if mmsi[:4] == "3669" and len(mmsi) == 7:
        return True
    return mmsi[:6] == "003369"


_ship_db_dict_cache: dict = {}


def get_ship_db_dict() -> dict:
    """Get ship database as dict indexed by MMSI for O(1) lookups."""
    global _ship_db_dict_cache
    if not _ship_db_dict_cache:
        ship_db = get_ship_db()
        _ship_db_dict_cache = {ship["MMSI"]: ship for ship in ship_db if "MMSI" in ship}
    return _ship_db_dict_cache


def get_shipname(mmsi: str) -> str:
    """Get the ship name from the Ship DB based on the MMSI.

    :param mmsi: MMSI of the ship.
    :returns: Ship name.
    """
    ship_db_dict = get_ship_db_dict()
    if ship := ship_db_dict.get(mmsi):
        return ship.get("name", "")
    return ""
