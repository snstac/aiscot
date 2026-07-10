## AISCoT 7.3.0

- AIS-catcher style vessel styling (mapping & palette re-implemented from
  [AIS-catcher](https://github.com/jvde-github/AIS-catcher)'s published behavior;
  no GPL assets copied):
  - New `aiscot.shipclass` module: MMSI + AIS ship type → ship class
    (tanker/cargo/passenger/special/highspeed/fishing/classb/aton/station/sartepirb).
  - `SHIPCLASS_COLORS` (default `True`): CoT `<color argb>` marker color by ship
    class — tankers red, cargo spring green, passenger blue, etc.
  - `SHIPCLASS_ICONS` (default `False`): CoT `<usericon>` from the new bundled
    `ais-ships-iconset.zip` ATAK iconset — dart when underway, circle when
    stopped, diamond for AtoN/base station/SART. `COT_ICON` still wins.
  - New `scripts/build_ais_iconset.py` regenerates the iconset (pure stdlib).
- `VESSEL_NAME_PREFIX` (default `True`): conventional ship-type callsign
  prefixes — `T/B Delores`, `P/V Golden Gate`, `M/V`, `M/T`, `F/V`, `S/V`, `SAR`,
  `A/P`, `L/E`. Already-prefixed and bare-MMSI callsigns pass verbatim.
- `UNDERWAY_ONLY` (default `False`): drop parked hulls (SOG < 0.5 kts, or
  anchored/moored/aground when SOG is missing). SOG outranks nav status; AtoN
  and USCG SAR/CRS are exempt.

## AISCoT 7.2.1

- Use PyTAK shared CoT event, point, detail, remarks, and serialization helpers.
- Require `pytak >= 7.3.12`.

## AISCoT 7.2.0

- Add `SensorWorker`: periodic `a-f-G-E-S-E` sensor CoT heartbeat every `SENSOR_KEEPALIVE_PERIOD` seconds (default 30).
- Position sourced from system gpsd → static `SENSOR_LAT`/`SENSOR_LON`/`SENSOR_HAE` config → null island fallback.
- Add `gen_sensor_cot()`: reusable CoT builder for sensor beacon events.
- New constants: `DEFAULT_SENSOR_KEEPALIVE_PERIOD=30`, `DEFAULT_SENSOR_LAT/LON/HAE=0.0`.

## AISCOT 7.1.4

- Limit reported position precision to a maximum of 4 decimal places (~11 m).

## AISCOT 7.1.0

- Happy New Year 2025!
- Performance Improvements.

## AISCOT 6.1.0

- Added support for DOT's SeaVision.
- Dropped support for Python 3.6

## AISCOT 6.0.0

- New for 2024.
- Updates for AryaSea (fka SeaTAK).

## AISCOT 5.3.0

Added COT_ICON support.

## AISCOT 5.2.0

1) Fixed GitHub workflows (revert to not-latest ubuntu, add py 3.10).
2) Reformatted & Cleaned-up README.
3) Updated copyright year.
4) Renamed 'AISHUB_URL' to 'FEED_URL'.
5) Added instructions for updating SHIP & MIB databases.
6) Removed broad function import in module's init.
7) Refactored AIS specific functions into ais_functions.
8) Added tests, tests, tests! Now at almost 100% for functions.

## AISCOT 5.1.0

Added XML Declaration to output CoT XML.
