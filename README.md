![Screenshot of ships in ATAK, via AISCOT.](https://aiscot.readthedocs.io/en/latest/media/aiscot_screenshot_tak_logo.png)

# AIS to TAK Gateway - Maritime Domain Awareness for Public Safety & Defense

AISCOT provides critical maritime domain awareness by streaming real-time vessel tracking data directly into Team Awareness Kit (TAK) platforms. This solution enables public safety professionals to monitor maritime activities with comprehensive situational awareness through native TAK integration.

## Key Capabilities

- **Real-time Maritime Tracking**: Continuous AIS data capture and reporting for immediate threat assessment
- **Native TAK Integration**: Seamless compatibility with ATAK, WinTAK, iTAK, TAK Server & TAKX using Cursor on Target (CoT) protocols
- **Multi-source Data Fusion**: Support for RF AIS transmissions, local NMEA feeds, and Internet-based AIS aggregators
- **Comprehensive Vessel Intelligence**: Display vessel icons, attitude, type, track history, bearing, speed, callsign, and maritime identifiers
- **AIS-catcher Style Vessel Markers**: Ship-class marker colors (tankers red, cargo green, passenger blue, ...), conventional callsign prefixes (``T/B``, ``P/V``, ``M/V``, ...), and an optional bundled ATAK iconset ([ais-ships-iconset.zip](https://github.com/snstac/aiscot/raw/main/src/aiscot/data/ais-ships-iconset.zip)) with dart/circle underway/stopped icons
- **Underway-only Filtering**: Optionally drop parked hulls (at anchor, moored, aground) so anchorage clutter doesn't drown the traffic picture
- **Government Data Access**: Integration with [US Department of Transportation SeaVision](https://seavision.volpe.dot.gov/) for enhanced coverage

## Use Cases

- **Port Security**: Monitor vessel approaches and harbor activities
- **Border Protection**: Track maritime border crossings and suspicious activities  
- **Search & Rescue**: Coordinate response efforts with real-time vessel positions
- **Intelligence Operations**: Analyze maritime patterns and vessel behaviors

## Documentation

[Complete AISCOT documentation and deployment guides](https://aiscot.rtfd.io)

## The snstac TAK sensor ecosystem

Different sensor, same workflow — pick the gateway for your application; most have a
matching Cockpit plugin for browser-based management:

| Application | Gateway | Cockpit plugin |
|---|---|---|
| Aircraft via ADS-B (1090 MHz / 978 MHz UAT) | [adsbcot](https://github.com/snstac/adsbcot) | [cockpit-adsbcot](https://github.com/snstac/cockpit-adsbcot) |
| Ships & vessels via AIS | [aiscot](https://github.com/snstac/aiscot) | [cockpit-aiscot](https://github.com/snstac/cockpit-aiscot), [cockpit-aiscatcher](https://github.com/snstac/cockpit-aiscatcher) |
| Drone / UAS Remote ID (counter-UAS) | [dronecot](https://github.com/snstac/dronecot) | [cockpit-dronecot](https://github.com/snstac/cockpit-dronecot) |
| Own position via GPS/GNSS | [lincot](https://github.com/snstac/lincot) | [cockpit-lincot](https://github.com/snstac/cockpit-lincot), [cockpit-gps](https://github.com/snstac/cockpit-gps) |
| Radio direction finding (KrakenSDR) | [kraktak](https://github.com/snstac/kraktak) | — |
| APRS amateur radio | [aprscot](https://github.com/snstac/aprscot) | — |
| Weather stations | [windtak](https://github.com/snstac/windtak) | — |
| CoT routing / TAK Server bridging | [charontak](https://github.com/snstac/charontak) | — |

All gateways are built on [PyTAK](https://github.com/snstac/pytak), speak
**Cursor on Target (CoT)** to **ATAK, WinTAK, iTAK, TAK Server, and Mesh SA**, ship as
signed Debian/RPM packages at [snstac.github.io/packages](https://snstac.github.io/packages),
and come pre-installed on [AryaOS](https://github.com/snstac/aryaos), the
situational-awareness OS for Raspberry Pi.


## License & Copyright

Copyright Sensors & Signals LLC https://www.snstac.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

* pyAISm.py is licensed under the MIT License. See aiscot/pyAISm.py for details.
