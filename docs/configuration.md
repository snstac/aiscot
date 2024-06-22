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

Additional configuration parameters, including TLS & TAK Server configuration, are included in the [PyTAK Configuration](https://pytak.readthedocs.io/en/stable/configuration/) documentation.
