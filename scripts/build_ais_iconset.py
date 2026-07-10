#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/build_ais_iconset.py from https://github.com/snstac/aiscot
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

"""Generate an ATAK user iconset with AIS-catcher-style vessel markers.

Produces ``src/aiscot/data/ais-ships-iconset.zip`` (import via ATAK Settings
→ Tool Preferences → Point Dropper → Iconset Manager, or push through a TAK
server mission package). Layout: ``iconset.xml`` at the zip root, PNGs under
``Ships/``; CoT references them as
``{AIS_SHIPS_ICONSET_UID}/Ships/<name>.png`` (see
``aiscot.shipclass.vessel_iconsetpath``).

Shapes follow AIS-catcher's visual language — solid dart when underway,
circle when stopped, diamond for AtoN / base station / SART — but are drawn
from scratch here (AIS-catcher's own sprite sheet is GPLv3), colored with its
ship-class palette. Pure stdlib: no Pillow required.
"""
from __future__ import annotations

import struct
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiscot.shipclass import (  # noqa: E402
    AIS_SHIPS_ICONSET_FILENAME,
    AIS_SHIPS_ICONSET_GROUP,
    AIS_SHIPS_ICONSET_UID,
    SHIPCLASS_ATON,
    SHIPCLASS_HEX,
    SHIPCLASS_SARTEPIRB,
    SHIPCLASS_STATION,
    vessel_icon_name,
)

SIZE = 32          # ATAK usericon size
SUPERSAMPLE = 4    # 4x4 coverage sampling per pixel
OUTLINE_HEX = "#1A1A1A"
DIAMOND_CLASSES = (SHIPCLASS_ATON, SHIPCLASS_STATION, SHIPCLASS_SARTEPIRB)

# Design space is 20x20 (AIS-catcher sprite cell), centered shapes.
ARROW = [(10.0, 1.5), (17.0, 17.5), (10.0, 14.0), (3.0, 17.5)]
DIAMOND = [(10.0, 1.5), (18.5, 10.0), (10.0, 18.5), (1.5, 10.0)]
CIRCLE_CENTER, CIRCLE_R = (10.0, 10.0), 6.5


def _hex_rgb(hex_color: str) -> tuple:
    v = int(hex_color.lstrip("#"), 16)
    return (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF


def _scale_poly(poly: list, factor: float) -> list:
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in poly]


def _in_poly(x: float, y: float, poly: list) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _shape_tests(kind: str):
    """(inside_outline, inside_fill) predicates in 20x20 design space."""
    if kind == "circle":
        def outer(x, y):
            return (x - CIRCLE_CENTER[0]) ** 2 + (y - CIRCLE_CENTER[1]) ** 2 <= CIRCLE_R**2

        def inner(x, y):
            return (x - CIRCLE_CENTER[0]) ** 2 + (y - CIRCLE_CENTER[1]) ** 2 <= (CIRCLE_R - 1.2) ** 2

        return outer, inner
    poly = ARROW if kind == "arrow" else DIAMOND
    inner_poly = _scale_poly(poly, 0.80)
    return (lambda x, y: _in_poly(x, y, poly)), (lambda x, y: _in_poly(x, y, inner_poly))


def render_icon(kind: str, fill_hex: str) -> bytes:
    """RGBA PNG bytes for one icon."""
    outer, inner = _shape_tests(kind)
    fill = _hex_rgb(fill_hex)
    line = _hex_rgb(OUTLINE_HEX)
    ss = SUPERSAMPLE
    rows: list = []
    for py in range(SIZE):
        row = bytearray()
        for px in range(SIZE):
            f_hits = o_hits = 0
            for sy in range(ss):
                for sx in range(ss):
                    x = (px + (sx + 0.5) / ss) * 20.0 / SIZE
                    y = (py + (sy + 0.5) / ss) * 20.0 / SIZE
                    if inner(x, y):
                        f_hits += 1
                    elif outer(x, y):
                        o_hits += 1
            total = f_hits + o_hits
            if total == 0:
                row += b"\x00\x00\x00\x00"
                continue
            r = (fill[0] * f_hits + line[0] * o_hits) // total
            g = (fill[1] * f_hits + line[1] * o_hits) // total
            b = (fill[2] * f_hits + line[2] * o_hits) // total
            a = 255 * total // (ss * ss)
            row += bytes((r, g, b, a))
        rows.append(bytes(row))
    return _png_bytes(SIZE, SIZE, rows)


def _png_bytes(w: int, h: int, rows: list) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    raw = b"".join(b"\x00" + r for r in rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def build(out_path: Path) -> list:
    icons: dict = {}
    for shipclass, hex_color in SHIPCLASS_HEX.items():
        if shipclass in DIAMOND_CLASSES:
            icons[vessel_icon_name(shipclass, False)] = render_icon("diamond", hex_color)
        else:
            icons[vessel_icon_name(shipclass, True)] = render_icon("arrow", hex_color)
            icons[vessel_icon_name(shipclass, False)] = render_icon("circle", hex_color)

    entries = "\n".join(
        f'    <icon name="{name}" type2525b="a-u-S-X-M"/>' for name in sorted(icons)
    )
    iconset_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<iconset name="AIS Ships (AIS-catcher palette)" uid="{AIS_SHIPS_ICONSET_UID}"'
        ' version="1" defaultFriendly="a-f-S-X-M" defaultHostile="a-h-S-X-M"'
        ' defaultNeutral="a-n-S-X-M" defaultUnknown="a-u-S-X-M" skipResize="false">\n'
        f"{entries}\n"
        "</iconset>\n"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("iconset.xml", iconset_xml)
        for name in sorted(icons):
            zf.writestr(f"{AIS_SHIPS_ICONSET_GROUP}/{name}", icons[name])
    return sorted(icons)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    out = repo_root / "src" / "aiscot" / "data" / AIS_SHIPS_ICONSET_FILENAME
    names = build(out)
    print(f"wrote {out} ({len(names)} icons, uid {AIS_SHIPS_ICONSET_UID})")
    for n in names:
        print(f"  {AIS_SHIPS_ICONSET_GROUP}/{n}")
