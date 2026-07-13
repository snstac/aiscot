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

* **`VESSEL_NAME_PREFIX`**:
    * Default: ``True``

    Prepend the conventional ship-type prefix to vessel callsigns, the way mariners name traffic: ``T/B Delores`` (tug/towing), ``P/V Golden Gate`` (pilot), ``M/V`` (cargo), ``M/T`` (tanker), ``F/V`` (fishing), ``S/V`` (sailing), ``SAR``, ``A/P``, ``L/E``. Names already carrying a prefix pass verbatim; bare-MMSI callsigns stay bare, and operator-curated ``KNOWN_CRAFT`` names are never rewritten.

* **`SHIPCLASS_COLORS`**:
    * Default: ``True``

    Color each vessel marker by its AIS-catcher ship class (the de-facto standard AIS viewer palette): tankers red, cargo spring green, passenger blue, special craft (pilot/SAR/tug/law) brown, high-speed craft yellow, fishing deep pink, sailing/pleasure magenta, everything else light azure. Emitted as a CoT ``<color argb=".."/>`` detail element; works on any TAK client.

* **`SHIPCLASS_ICONS`**:
    * Default: ``False``

    Set each vessel marker's icon by ship class from the bundled ``ais-ships-iconset.zip`` ATAK iconset: solid dart when underway, circle when stopped, diamond for AtoN / base station / SART, colored with the AIS-catcher palette. Clients must import the iconset first (ATAK Settings → Tool Preferences → Point Dropper → Iconset Manager), so this is opt-in. ``COT_ICON`` still takes precedence. The zip ships with the package under ``aiscot/data/`` and can be regenerated with ``scripts/build_ais_iconset.py``.

* **`UNDERWAY_ONLY`**:
    * Default: ``False``

    Only forward vessels that are underway (SOG ≥ 0.5 knots, or a non-parked navigation status when SOG is missing); parked hulls (at anchor, moored, aground) are dropped. At busy anchorages the marina clutter otherwise drowns the underway traffic picture. SOG outranks navigation status — crews leave "Underway" set at the dock and "Moored" set while sailing (the AIS "SOG not available" sentinel falls through to navigation status). Vessels reporting neither SOG nor navigation status pass through. Never dropped: AtoN, USCG SAR/CRS craft, SART/EPIRB/MOB distress beacons, and vessels listed in ``KNOWN_CRAFT``.

Additional configuration parameters, including TLS & TAK Server configuration, are included in the [PyTAK Configuration](https://pytak.readthedocs.io/en/stable/configuration/) documentation.
