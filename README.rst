AISCOT - AIS Cursor on Target Gateway
*************************************

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/2023_updates/docs/screenshot_1676076870_2962.png
   :alt: Screenshot of AIS as COT PLI in ATAK.
   :target: https://raw.githubusercontent.com/ampledata/aiscot/2023_updates/docs/screenshot_1676076870_2962.png

Description
===========

The Automatic Identification System to Cursor on Target gateway (AISCOT) transforms 
automatic identification system (AIS) to Cursor on Target (CoT) for use with TAK 
products such as ATAK, WinTAK & iTAK. Vessels sending AIS either 
over the air (RF), through a local networks (NMEA), or through internet aggregators 
(AISHUB), will be displayed in TAK with appropriate icons, attitude, type, track, 
bearing, speed, callsign and more.

For more information the TAK Product suite, see: https://ww.tak.gov

AISCOT was original developed to support an open ocean boat race in the Northern 
Pacific Ocean, as described in this article: http://ampledata.org/boat_race_support.html


Concept of Operations
=====================

AISCOT can operate in two different modes, as described in detail below:

1. AIS Over-the-air (RF)
2. AIS Aggregator (AISHUB)

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


Support Development
===================

.. image:: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
    :target: https://www.buymeacoffee.com/ampledata
    :alt: Support Development: Buy me a coffee!


Installation
============

**AISCOT requires Python 3.6 or above.**

AISCOT functionality is provided by a command-line tool called ``aiscot``, which can be 
installed several ways.

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

Command-line options::

    usage: aiscot [-h] [-c CONFIG_FILE] [-p PREF_PACKAGE]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG_FILE, --CONFIG_FILE CONFIG_FILE
                            Optional configuration file. Default: config.ini
    -p PREF_PACKAGE, --PREF_PACKAGE PREF_PACKAGE
                            Optional connection preferences package zip file (aka Data Package).

Configuration options:
    ``COT_URL`` : str,  default: udp://239.2.3.1:6969
        URL to CoT destination. Must be a URL, e.g. ``tcp://1.2.3.4:1234`` or ``tls://...:1234``, etc. See `PyTAK <https://github.com/ampledata/pytak#configuration-parameters>`_ for options, including TLS support.
    ``AIS_PORT`` : int, default: 5050
        AIS UDP Listen Port, for use with Over-the-air (RF) AIS.
    ``COT_STALE`` : int, default: 3600
        CoT Stale period ("timeout"), in seconds. Default `3600` seconds (1 hour).
    ``COT_TYPE`` : str, default: a-u-S-X-M
        Override COT Event Type ("marker type").
    ``FEED_URL`` : str, optional
        AISHUB feed URL. See **AISHUB usage notes** in README below.
    ``KNOWN_CRAFT`` : str, optional
        Known Craft hints file. CSV file containing callsign/marker hints.
    ``INCLUDE_ALL_CRAFT`` : bool, optional
        If using KNOWN_CRAFT, still include other craft not in our KNOWN_CRAFT list.
    ``IGNORE_ATON`` : bool, optional
        IF SET- adsbcot will ignore AIS from Aids to Naviation (buoys, etc).

See example-config.ini in the source tree for example configuration.

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
forwarding COT to a TAK Server and WinTAK & ATAK clients. (OV-1)


.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/aiscot_home.png
   :alt: AISCOT Example setup


Database Update
===============
Occasional updates to the YADD Ship Name database can be found at: http://www.yaddnet.org/pages/php/test/tmp/

Updates to the MID database can be found at: TK  


Source
======
Github: https://github.com/ampledata/aiscot


Author
======
Greg Albrecht oss@undef.net

http://ampledata.org/


Copyright
=========

* aiscot Copyright 2023 Greg Albrecht <oss@undef.net>
* pyAISm.py Copyright 2016 Pierre Payen


License
=======

Copyright 2023 Greg Albrecht <oss@undef.net>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

* pyAISm.py is licensed under the MIT License. See aiscot/pyAISm.py for details.
