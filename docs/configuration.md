AISCOT supports multiple methods of configuration:

1. INI-style config file, see `config.example.ini`. Usage: `aiscot -c config.ini`.
2. Environment variables. Usage: `export DEBUG=1 ; aiscot`
3. If using systemd, edit `/etc/default/aiscot`

AISCOT has the following built-in configuration parameters:

* **`COT_URL`**
    * Default: ``udp+wo://239.2.3.1:6969`` (TAK Mesh SA, Multicast UDP, write-only)

    Destination for TAK Data (Cursor on Target Events). Supported values are:
    
    * TLS Unicast: ``tls://host:port``
    * TCP Unicast: ``tcp://host:port``
    * UDP Multicast: ``udp://group:port`` (aka **Mesh SA**)
    * UDP Unicast: ``udp://host:port``
    * UDP Broadcast: ``udp+broadcast://network:port``
    * UDP Write-only: ``udp+wo://host:port``
    * stdout or stderr: ``log://stdout`` or ``log://stderr``

    **N.B.** `+wo` modifier stands for 'write-only', and allows multiple PyTAK 
    applications to run on a single bound-interface without monopolizing a port. If you're getting a 'cannot bind to port' or 'port occupied error', try adding the `+wo` modifier.

* **`AIS_PORT`**:
    * Default: ``5050`` 

    AIS UDP Listen Port, for use with Over-the-air (RF) AIS.
    
* **`COT_STALE`**:
    * Default: ``3600`` (seconds)

    CoT Stale period ("timeout"), in seconds.

* **`COT_TYPE`**:
    * Default: ``a-u-S-X-M``
    
    Override COT Event Type ("marker type").

* **`COT_ICON`**:
    * Default:

    Set a custom user icon / custom marker icon in TAK. Contains a Data Package UUID and resource name (file name).

* **`KNOWN_CRAFT`**:
    * Default: unset

    CSV-style hints file for overriding callsign, icon, COT Type, etc.

* **`INCLUDE_ALL_CRAFT`**:
    * Default: ``False``

    If ``True`` and ``KNOWN_CRAFT`` is set, will forward all craft, including those transformed by the ``KNOWN_CRAFT`` database.

* **`IGNORE_ATON`**:
    * Default: ``False``

    Ignore AIS from Aids to Naviation (buoys, etc).

## AISStream.io Integration

AISCOT supports integration with [AISStream.io](https://aisstream.io/), a websocket-based API for real-time maritime data. To use AISStream integration, do not set a `FEED_URL` in your configuration.

* **`AISSTREAM_API_KEY`**:
    * Default: unset

    Your AISStream.io API key (get one at [aisstream.io](https://aisstream.io/))

* **`BBOX_LAT_MIN`**, **`BBOX_LON_MIN`**, **`BBOX_LAT_MAX`**, **`BBOX_LON_MAX`**:
    * Default: unset

    Bounding box coordinates for the area you want to monitor. 
    
    **IMPORTANT**: AISStream.io uses [latitude, longitude] format, which is the opposite of many mapping systems that use [longitude, latitude]. Getting this wrong will result in no data being received or monitoring the wrong region.
    
    Valid latitude values are between -90 and 90 degrees.
    Valid longitude values are between -180 and 180 degrees.
    
    Example for Gulf of Mexico region:
    ```
    BBOX_LAT_MIN = 18
    BBOX_LON_MIN = -98
    BBOX_LAT_MAX = 30
    BBOX_LON_MAX = -82
    ```

* **`AISSTREAM_MESSAGE_TYPES`**:
    * Default: unset (all message types)

    Comma-separated list of message types to receive from AISStream.io. Common types include:
    - `PositionReport` - Basic position reports (most common)
    - `ShipStaticData` - Ship details like name, callsign, etc.
    - `StandardClassBPositionReport` - Position reports from Class B transponders
    - `ExtendedClassBPositionReport` - Extended position reports from Class B transponders

    Full list of available types: PositionReport, UnknownMessage, AddressedSafetyMessage, AddressedBinaryMessage, AidsToNavigationReport, AssignedModeCommand, BaseStationReport, BinaryAcknowledge, BinaryBroadcastMessage, ChannelManagement, CoordinatedUTCInquiry, DataLinkManagementMessage, DataLinkManagementMessageData, ExtendedClassBPositionReport, GroupAssignmentCommand, GnssBroadcastBinaryMessage, Interrogation, LongRangeAisBroadcastMessage, MultiSlotBinaryMessage, SafetyBroadcastMessage, ShipStaticData, SingleSlotBinaryMessage, StandardClassBPositionReport, StandardSearchAndRescueAircraftReport, StaticDataReport.

* **`VESSEL_CACHE_FILE`**:
    * Default: unset (in-memory only)

    Optional file path for persisting vessel names between application restarts. The registry uses this file to save and load vessel information (MMSI to name mappings), which helps maintain consistent vessel identification even when ships only transmit their static data (name, callsign, etc.) infrequently.
    
    Example:
    ```
    VESSEL_CACHE_FILE = vessel_names.json
    ```

Additional configuration parameters, including TLS & TAK Server configuration, are included in the [PyTAK Configuration](https://pytak.readthedocs.io/en/stable/configuration/) documentation.
