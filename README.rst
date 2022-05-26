aiscot - AIS Cursor-on-Target Gateway.
****************************************

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/screenshot-1601068921-25.png
   :alt: Screenshot of AIS as COT PLI in ATAK.
   :target: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/screenshot-1601068921.png

**IF YOU HAVE AN URGENT OPERATIONAL NEED**: Email: ops@undef.net or Signal: +1-415-598-8226

AISCOT transforms AIS data to Cursor-On-Target for display on Situational Awareness 
applications like ATAK, WinTAK, iTAK, TAKX, COPERS, et al. See https://www.tak.gov/ 
for more information on the TAK program.

AISCOT was original developed to support an open ocean boat race in the Northern 
Pacific Ocean, as described in this article: http://ampledata.org/boat_race_support.html

AISCOT Concept of Operation
===========================

AISCOT can operate in two different modes, as described in detail below:

1. AIS Over-the-air
2. AIS Aggregator

**AIS Over-the-air Operation (RF)**

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/aiscot_ota.png
   :alt: AISCOT "AIS Over the Air" Operation

Receive AIS data from a VHF AIS receiver, such as the 
Megwatt `dAISy+ <https://shop.wegmatt.com/products/daisy-ais-receiver>`_. From there 
AIS can be decoded by `AIS Dispatcher <https://www.aishub.net/ais-dispatcher>`_ and 
forwarded to AISCOT to be transformed to COT and transmitted to COT destinations.

**AIS Aggregator Operation (AISHUB.com)**

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/aiscot_agg.png
   :alt: AISCOT "AIS Aggregator" Operation

Receive AIS data from the `AISHUB <https://www.aishub.com>`_ service. 
Requires a subscription to AISHUB.

Support AISCOT Development
==========================

AISCOT has been developed for the Disaster Response, Public Safety and 
Frontline community at-large. This software is currently provided at no-cost to 
our end-users. Any contribution you can make to further these software development 
efforts, and the mission of AISCOT to provide ongoing SA capabilities to our 
end-users, is greatly appreciated:

.. image:: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
    :target: https://www.buymeacoffee.com/ampledata
    :alt: Support AISCOT development: Buy me a coffee!


Installation
============

AISCOT functionality is provided by a command-line tool called `aiscot`, 
which can be installed several ways.

**AISCOT requires Python 3.6 or above.**

Installing as a Debian/Ubuntu Package [Use Me!]::

    $ wget https://github.com/ampledata/pytak/releases/latest/download/python3-pytak_latest_all.deb
    $ sudo apt install -f ./python3-pytak_latest_all.deb
    $ wget https://github.com/ampledata/aiscot/releases/latest/download/python3-aiscot_latest_all.deb
    $ sudo apt install -f ./python3-aiscot_latest_all.deb

Install from the Python Package Index [Alternative]::

    $ python3 -m pip install -U pytak
    $ python3 -m pip install -U aiscot

Install from this source tree [Developer]::

    $ git clone https://github.com/ampledata/aiscot.git
    $ cd aiscot/
    $ python3 setup.py aiscot


Usage
=====

AISCOT can be configured with a INI-style configuration file, or using 
environmental variables.

Command-line options:
      -h, --help            show this help message and exit
      -c CONFIG_FILE, --CONFIG_FILE     If specified, use this config file. Default 'config.ini'.

Configuration options:
    COT_URL : str,  default: udp://239.2.3.1:6969
        URL to COT destination. Must be a URL, e.g. ``tcp://1.2.3.4:1234`` or ``tls://...:1234``, etc.
    AIS_PORT : int, default: 5050
        AIS UDP Listen Port.
    COT_STALE : int, default: 3600
        CoT Stale period ("timeout"), in seconds. Default `3600` seconds (1 hour).
    COT_TYPE : str, default: a-u-S-X-M
        Override COT Event Type ("marker type").
    AISHUB_URL : str, optional
        AISHUB feed URL. See **AISHUB usage notes** in README below.
    KNOWN_CRAFT : str, optional
        Known Craft hints file. CSV file containing callsign/marker hints.
    INCLUDE_ALL_CRAFT : bool, optional
        If using KNOWN_CRAFT, still include other craft not in our KNOWN_CRAFT list.

See example-config.ini in the source tree for example configuration.

**COT destination notes**

The ``COT_URL`` configuration option must be specified as a fully-qualified URL. By 
default this tool will send COT to the default ATAK & WinTAK network multicast UDP 
group & port: ``udp://239.2.3.1:6969``. You can specify other destinations by either 
setting the ``COT_URL`` configuration option in the config INI, or by setting the ``COT_URL`` 
environmental variable.

Example ``COT_URL``:

* ``tcp://172.17.2.100:4242`` : Send COT as TCP to host 172.17.2.100 on port 4242.

* ``tls://192.168.2.1:8089`` : Send COT as TLS to host 192.168.2.1 on port 8089. Requires setting additional environmental variables, see `PyTAK TLS documentation <https://github.com/ampledata/pytak#tls-support>`_.

* ``udp://10.0.1.99:8087`` : Send COT as unicast UDP to host 10.0.1.99 on port 8087.


**AISHUB usage notes**

AISHUB.com requires registration. Once registered the site will provide you with a
Username that you'll use with their feed. You'll also need to specify a Bounding Box 
when accessing the feed. 

The AISHUB_URL must be specified as follows:

``https://data.aishub.net/ws.php?format=1&output=json&compress=0&username=AISHUB_USERNAME&latmin=BBOX_LAT_MIN&latmax=BBOX_LAT_MAX&lonmin=BBOX_LON_MON&lonmax=BBOX_LON_MAX``

Replacing ``AISHUB_USERNAME`` with your AISHUB.com username, and specifying the 
Bounding Box is specified as follows:

latmin : signed float
    The minimum latitude of the Bounding Box (degrees from Equator) as a signed float 
    (use negative sign for East: ``-``).
latmax : signed float
    The maximum latitude of the Bounding Box (degrees from Equator) as a signed float
    (use negative sign for East: ``-``).
lonmin : signed float
    The minimum longitude of the Bound Box (degrees from Prime Meridian) as a signed float
    (use negative sign for North: ``-``).
lonmax : signed float
    The maximum longitude of the Bound Box (degrees from Prime Meridian) as a signed float 
    (use negative sign for North: ``-``).

For example, the following Bound Box paints a large swath around Northern California: 
``latmin=35&latmax=38&lonmin=-124&lonmax=-121``. This can be read as: 
"Between 35° and 38° latitude & -121° and -124° longitude".



Example Setup
=============

The following diagram shows an example setup of AISCOT utilizing a dAISy+ AIS receiver 
with an outboard Marine VHF antenna, a Raspberry Pi running aisdispatcher and AISCOT, 
forwarding COT to a TAK Server and WinTAK & ATAK clients.


.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/aiscot_home.png
   :alt: AISCOT Example setup


Source
======
Github: https://github.com/ampledata/aiscot


Author
======
Greg Albrecht W2GMD oss@undef.net

http://ampledata.org/


Copyright
=========

* aiscot Copyright 2022 Greg Albrecht
* pyAISm.py Copyright 2016 Pierre Payen


License
=======

* aiscot is licensed under the Apache License, Version 2.0. See LICENSE for details.
* pyAISm.py is licensed under the MIT License. See aiscot/pyAISm.py for details.
