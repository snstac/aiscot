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

import xml.etree.ElementTree as ET

from configparser import SectionProxy
from typing import Optional, Union
from xml.etree.ElementTree import tostring, Element

import pytak
import aiscot
import aiscot.ais_functions as aisfunc


def create_tasks(config: Union[dict, SectionProxy], clitool: pytak.CLITool) -> set:
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
def ais_to_cot_xml(
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

    lat: float = float(craft.get("lat", craft.get("LATITUDE", "0")))
    lon: float = float(craft.get("lon", craft.get("LONGITUDE", "0")))
    mmsi: str = str(craft.get("mmsi", craft.get("MMSI", "")))
    # At least these three must exist, but may have different names depending on the
    # AIS source:
    if not all([lat, lon, mmsi]):
        return None

    aton: bool = aisfunc.get_aton(mmsi)
    # If IGNORE_ATON is set and this is an Aid to Naviation, we'll ignore it.
    if aton and config.get("IGNORE_ATON"):
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

    aiscotx: Element = Element("_aiscot_")
    aiscotx.set("cot_host_id", cot_host_id)

    ais_name: str = (
        str(craft.get("name", craft.get("NAME", ""))).replace("@", "").strip()
    )
    shipname: str = str(craft.get("shipname", aisfunc.get_shipname(mmsi)))
    vessel_type: str = str(craft.get("type", craft.get("TYPE", "")))

    cot_icon = config.get("COT_ICON")

    if ais_name:
        remarks_fields.append(f"AIS Name: {ais_name}")
        aiscotx.set("ais_name", ais_name)

    if shipname:
        ais_name = shipname
        remarks_fields.append(f"Shipname: {shipname}")
        aiscotx.set("shipname", shipname)

    _name = known_craft.get("NAME") or ais_name
    if _name:
        callsign = _name
    else:
        callsign = mmsi

    country: str = aisfunc.get_mid(mmsi)
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

    aiscotx.set("aton", str(aton))
    if aton:
        cot_type = "a-n-S-N"
        cot_stale = 86400  # 1 Day
        callsign = f"AtoN {callsign}"
        remarks_fields.append(f"AtoN: {aton}")

    uscg: bool = aisfunc.get_sar(mmsi)
    aiscotx.set("uscg", str(uscg))
    if uscg:
        cot_type = "a-f-S-X-L"
        remarks_fields.append(f"USCG: {uscg}")

    crs: bool = aisfunc.get_crs(mmsi)
    aiscotx.set("crs", str(crs))
    if crs:
        cot_type = "a-f-G-I-U-T"
        cot_stale = 86400  # 1 Day
        callsign = f"USCG CRS {callsign}"
        remarks_fields.append(f"USCG CRS: {crs}")

    point = Element("point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", "9999999.0")
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    track = Element("track")
    heading: Optional[float] = craft.get("heading", craft.get("HEADING"))
    if heading:
        track.set("course", str(heading))

    # AIS Speed over ground: 0.1-knot (0.19 km/h) resolution from
    #                    0 to 102 knots (189 km/h)
    # COT Speed is meters/second
    sog: Optional[float] = craft.get("speed", craft.get("SPEED"))
    if sog:
        sog = float(sog) * 0.1 / 1.944
    if sog and sog != 0.0:
        track.set("speed", str(sog))

    # Contact
    contact = Element("contact")
    contact.set("callsign", str(callsign))

    remarks = Element("remarks")
    remarks_fields.append(f"{cot_host_id}")
    _remarks = " ".join(list(filter(None, remarks_fields)))
    remarks.text = _remarks

    detail = Element("detail")
    detail.append(track)
    detail.append(contact)
    detail.append(remarks)

    if cot_icon:
        usericon = ET.Element("usericon")
        usericon.set("iconsetpath", cot_icon)
        detail.append(usericon)

    root = Element("event")
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
    craft: dict,
    config: Union[dict, SectionProxy, None] = None,
    known_craft: Optional[dict] = None,
) -> Optional[bytes]:
    """Convert AIS to CoT XML and return it as 'TAK Protocol, Version 0'.

    'TAK Protocol, Version 0' being:
     1. XML Declaration.
     2. Newline.
     3. Cursor on Target <event/> Element.
     4. Newline.
    """
    cot: Optional[Element] = ais_to_cot_xml(craft, config, known_craft)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, tostring(cot), b""]) if cot else None
    )
