aiscot - AIS Cursor-on-Target Gateway.
****************************************

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/screenshot-1601068921-25.png
   :alt: Screenshot of AIS as COT PLI in ATAK.
   :target: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/screenshot-1601068921.png

**IF YOU HAVE AN URGENT OPERATIONAL NEED**: Email: ops@undef.net or Signal: +1-415-598-8226

AISCOT transforms AIS data to Cursor-On-Target for display on Situational Awareness 
applications like ATAK, WinTAK, iTAK, TAKX, COPERS, et al. See https://www.tak.gov/ 
for more information on the TAK program.

AISCOT has two modes of operation:

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/aiscot_ota.png
   :alt: AISCOT "AIS Over the Air" Operation

1. Over-the-air AIS: Receives AIS data from a VHF AIS receiver, such as the 
Megwatt `dAISy+ <https://shop.wegmatt.com/products/daisy-ais-receiver>`_. From there 
AIS can be decoded by `AIS Dispatcher <https://www.aishub.net/ais-dispatcher>`_ and 
forwarded to AISCOT to be transformed to COT and transmitted to COT destinations.

.. image:: https://raw.githubusercontent.com/ampledata/aiscot/main/docs/aiscot_agg.png
   :alt: AISCOT "AIS Aggregator" Operation

2. AIS Aggregator feeds: Receives AIS data from the `AISHUB <https://www.aishub.com>`_ service. 
Requires a subscription to AISHUB.


AISCOT was original developed to support an open ocean boat race in the Northern 
Pacific Ocean, as described in this article: http://ampledata.org/boat_race_support.html

Support AISCOT Development
==========================

AISCOT has been developed for the Disaster Response, Public Safety and 
Frontline community at-large. This software is currently provided at no-cost to 
our end-users. All development is self-funded and all time-spent is entirely
voluntary. Any contribution you can make to further these software development 
efforts, and the mission of AISCOT to provide ongoing SA capabilities to our 
end-users, is greatly appreciated:

.. image:: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
    :target: https://www.buymeacoffee.com/ampledata
    :alt: Support AISCOT development: Buy me a coffee!

Installation
============


AISCOT functionality is provided by a command-line tool called `aiscot`, 
which can be installed several ways.

Installing as a Debian/Ubuntu Package [Use Me!]::

    $ wget https://github.com/ampledata/pytak/releases/latest/download/python3-pytak_latest_all.deb
    $ sudo apt install -f ./python3-pytak_latest_all.deb
    $ wget https://github.com/ampledata/aiscot/releases/latest/download/python3-aiscot_latest_all.deb
    $ sudo apt install -f ./python3-aiscot_latest_all.deb

Install from the Python Package Index [Alternative]::

    $ pip install aiscot

Install from this source tree [Developer]::

    $ git clone https://github.com/ampledata/aiscot.git
    $ cd aiscot/
    $ python setup.py aiscot


Usage
=====

AISCOT can be configured with a INI-style configuration file, or using 
environmental variables.

Command-line options:
      -h, --help            show this help message and exit
      -c CONFIG_FILE, --CONFIG_FILE     If specified, use this config file. Default 'config.ini'.

Configuration options:
    COT_URL : `str`
        URL to COT destination. Must be a URL, e.g. `tcp://1.2.3.4:1234` or `tls://...:1234`, etc. Default `udp://239.2.3.1:6969`
    AIS_PORT : `int`
        AIS UDP Listen Port.
    COT_STALE : `int`
        CoT Stale period ("timeout"), in seconds. Default `3600` seconds (1 hour).
    KNOWN_CRAFT : `str`
        Known Craft hints file. CSV file containing callsign/marker hints.
    INCLUDE_ALL_CRAFT : `bool`
        If using KNOWN_CRAFT, still include other craft not in our KNOWN_CRAFT list.
    COT_TYPE : `str`
        Override COT Event Type ("marker type"). Default `a-u-S-X-M`.

See example-config.ini in the source tree for example configuration.


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
