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
