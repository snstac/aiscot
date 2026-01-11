#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# functions.py from https://github.com/snstac/aiscot
#
# Copyright Sensors & Signals LLC https://www.snstac.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""AISCOT functions for parsing AIS and generating Cursor on Target."""

import os
import logging
import xml.etree.ElementTree as ET

from configparser import SectionProxy
from typing import Optional, Set, Union
from xml.etree.ElementTree import tostring, Element

import pytak
import aiscot
import aiscot.ais_functions as aisfunc

APP_NAME = "aiscot"
Logger = logging.getLogger(__name__)
Debug = bool(os.getenv("DEBUG", False))


def create_tasks(
    config: Union[dict, SectionProxy], clitool: pytak.CLITool
) -> Set[pytak.Worker,]:
    """Bootstrap a set of coroutine tasks for a PyTAK application.

    Bootstrapped tasks:
        1) Receive Queue Worker
        2) Transmit Queue Worker

    This application adds:
        `aiscot.AISWorker`

    Parameters
    ----------
    config : `dict`, `SectionProxy`
        `dict` or `SectionProxy` of configuration parameters & values.
    clitool : `pytak.CLITool`
        PyTAK CLITool instance.

    Returns
    -------
    `set`
        Set of coroutine tasks.
    """
    return set([aiscot.AISWorker(clitool.tx_queue, config)])


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def ais_to_cot(
    craft: dict,
    config: Union[dict, SectionProxy, None] = None,
    known_craft: Optional[dict] = None,
) -> Optional[Element]:
    """Convert AIS sentences to Cursor on Target.

    Supports AIS from different sources, including Serial/NMEA and API feeds.

    Parameters
    ----------
    craft : De-serialized AIS.
    config : Configuration parameters for AISCOT.
    known_craft : Transforms for AIS data.

    Returns
    -------
    A Cursor on Target <event/>.
    """
    known_craft = known_craft or {}
    config = config or {}
    remarks_fields: list = []

    # Extract and validate required fields with optimized lookups
    lat: float = float(
        craft.get("lat") or craft.get("LATITUDE") or craft.get("latitude") or "0"
    )
    lon: float = float(
        craft.get("lon") or craft.get("LONGITUDE") or craft.get("longitude") or "0"
    )
    mmsi: str = str(craft.get("mmsi") or craft.get("MMSI") or "")

    # At least these three must exist, but may have different names depending on the
    # AIS source:
    if Debug:
        Logger.debug(f"lat={lat} lon={lon} mmsi={mmsi}")
    if not all([lat, lon, mmsi]):
        Logger.error("Missing lat, lon, or mmsi.")
        return None

    aton: bool = aisfunc.get_aton(mmsi)
    # If IGNORE_ATON is set and this is an Aid to Naviation, we'll ignore it.
    if aton and config.get("IGNORE_ATON"):
        if Debug:
            Logger.debug(f"Ignoring AtoN: {mmsi}")
        return None

    uid: str = f"MMSI-{mmsi}"

    # N.B. SectionProxy does not support dict's "fallback" parameter, you have to
    #      use explicit conditionals ('or'), like so:
    cot_type: str = str(
        config.get("COT_TYPE") or known_craft.get("COT") or aiscot.DEFAULT_COT_TYPE
    )

    cot_stale: int = int(
        config.get("COT_STALE") or known_craft.get("STALE") or aiscot.DEFAULT_COT_STALE
    )

    cot_host_id: str = str(config.get("COT_HOST_ID") or "")
    cot_icon = config.get("COT_ICON")
    cot_access = config.get("COT_ACCESS", pytak.DEFAULT_COT_ACCESS)

    xais: Element = Element("__ais")
    xais.set("cot_host_id", cot_host_id)

    # Optimize name extraction - avoid redundant str() conversions
    ais_name_raw = craft.get("name") or craft.get("NAME") or ""
    ais_name: str = str(ais_name_raw).replace("@", "").strip() if ais_name_raw else ""
    
    shipname: str = ""
    if temp := (craft.get("shipname") or aisfunc.get_shipname(mmsi)):
        shipname = str(temp)
    
    vessel_type: str = ""
    if temp := (craft.get("type") or craft.get("TYPE") or craft.get("veselType")):
        vessel_type = str(temp)

    if ais_name:
        remarks_fields.append(f"AIS Name: {ais_name}")
        xais.set("ais_name", ais_name)

    if shipname:
        ais_name = shipname
        remarks_fields.append(f"Shipname: {shipname}")
        xais.set("shipname", shipname)

    _name = known_craft.get("NAME") or ais_name
    if _name:
        callsign = _name
    else:
        callsign = mmsi

    country: str = aisfunc.get_mid(mmsi)
    if country:
        cot_type = "a-n" + cot_type[3:]
        remarks_fields.append(f"Country: {country}")
        xais.set("country", country)
        if "United States of America" in country:
            cot_type = "a-f" + cot_type[3:]

    if vessel_type:
        remarks_fields.append(f"Type: {vessel_type}")
        xais.set("vessel_type", vessel_type)

    remarks_fields.append(f"MMSI: {mmsi}")
    xais.set("mmsi", mmsi)

    xais.set("aton", str(aton))
    if aton:
        cot_type = "a-n-S-N"
        cot_stale = 86400  # 1 Day
        callsign = f"AtoN {callsign}"
        remarks_fields.append(f"AtoN: {aton}")

    uscg: bool = aisfunc.get_sar(mmsi)
    xais.set("uscg", str(uscg))
    if uscg:
        cot_type = "a-f-S-X-L"
        remarks_fields.append(f"USCG: {uscg}")

    crs: bool = aisfunc.get_crs(mmsi)
    xais.set("crs", str(crs))
    if crs:
        cot_type = "a-f-G-I-U-T"
        cot_stale = 86400  # 1 Day
        callsign = f"USCG CRS {callsign}"
        remarks_fields.append(f"USCG CRS: {crs}")

    track = Element("track")
    heading: Optional[float] = craft.get("heading", craft.get("HEADING"))
    if heading:
        track.set("course", str(heading))

    # AIS Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    # COT Speed is meters/second
    # Pre-computed constant: 0.1 / 1.944 = 0.05144
    if sog := (craft.get("speed") or craft.get("SPEED") or craft.get("SOG")):
        sog_ms = float(sog) * 0.05144
        if sog_ms != 0.0:
            track.set("speed", str(sog_ms))

    # Contact
    contact = Element("contact")
    contact.set("callsign", str(callsign))

    remarks = Element("remarks")
    if cot_host_id:
        remarks_fields.append(cot_host_id)
    remarks.text = " ".join(remarks_fields)

    detail = Element("detail")
    detail.append(track)
    detail.append(contact)
    detail.append(remarks)
    detail.append(xais)

    if cot_icon:
        usericon = ET.Element("usericon")
        usericon.set("iconsetpath", cot_icon)
        detail.append(usericon)

    cot_d = {
        "lat": str(lat),
        "lon": str(lon),
        "ce": "9999999.0",
        "le": "9999999.0",
        "hae": "0.0",
        "uid": uid,
        "cot_type": cot_type,
        "stale": cot_stale,
    }
    cot = pytak.gen_cot_xml(**cot_d)
    cot.set("access", cot_access)

    _detail = cot.findall("detail")[0]
    flowtags = _detail.findall("_flow-tags_")
    detail.extend(flowtags)
    cot.remove(_detail)
    cot.append(detail)

    return cot


def cot_to_xml(
    data: dict,
    config: Union[SectionProxy, dict, None] = None,
    known_craft: Optional[dict] = None,
    func: Optional[str] = None,
) -> Optional[bytes]:
    """Return a CoT XML object as an XML string, using the given func."""
    func = func or "ais_to_cot"
    cot: Optional[ET.Element] = getattr(aiscot.functions, func)(
        data, config, known_craft
    )
    if cot is not None:
        return b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)])
    if Debug:
        Logger.debug("No CoT XML generated.")
    return None
