aiscot - AIS Cursor-on-Target Gateway.
****************************************
**IF YOU HAVE AN URGENT OPERATIONAL NEED**: Email ops@undef.net or call/sms +1-415-598-8226

.. image:: docs/screenshot-1601068921-25.png
   :alt: Screenshot of AIS points in ATAK-Div Developer Edition.
   :target: docs/screenshot-1601068921.png


aiscot receives AIS Sentences from an AIS Receiver, such as ais-decoder,
converts them to Cursor-on-Target Events, and transmits the CoT Events to a destination.

For use with CoT systems such as ATAK, WinTAK, etc. See https://www.civtak.org/ for more information on the TAK
program.

Utilized for an open ocean boat race in the Northern Pacific Ocean, as
described in this article: http://ampledata.org/boat_race_support.html

Support AISCoT Development
==========================

AISCoT Software development is powered by coffee! Since we probably won't be able to meet in person any time soon, you
can buy me a virtual coffee here:

.. image:: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
    :target: https://www.buymeacoffee.com/ampledata
    :alt: Support AISCoT development: Buy me a coffee!

Installation
============

The command-line daemon `aiscot` can be install from this source tree (A), or from
the Python Package Index (PyPI) (B).

A) To install from this source tree::

    $ git checkout https://github.com/ampledata/aiscot.git
    $ cd aiscot/
    $ python setup.py install

B) To install from PyPI::

    $ pip install aiscot


Usage
=====

The `aiscot` daemon has several runtime arguments::

    $ aiscot --help
    usage: aiscot [-h] [-P AIS_PORT] -C COT_HOST

    optional arguments:
      -h, --help            show this help message and exit
      -P AIS_PORT, --ais_port AIS_PORT
                            AIS UDP Port
      -C COT_HOST, --cot_host COT_HOST
                            Cursor-on-Target Host or Host:Port

For minimum operation, `-P AIS_PORT` & `-C COT_HOST` are required.

The following example listens for AIS Sentences on UDP 0.0.0.0:5050, and
forwards CoT messages to UDP 172.17.2.222:4242::

  $ aiscot -P 5050 -C 172.17.2.222:4242


Source
======
Github: https://github.com/ampledata/aiscot

Author
======
Greg Albrecht W2GMD oss@undef.net

http://ampledata.org/

Copyright
=========
Copyright 2021 Orion Labs, Inc.

License
=======
Apache License, Version 2.0. See LICENSE for details.
