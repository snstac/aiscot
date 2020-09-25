aiscot - AIS Cursor-on-Target Gateway.
****************************************

.. image:: docs/screenshot-1601068921-25.png
   :alt: Screenshot of AIS points in ATAK-Div Developer Edition.
   :target: docs/screenshot-1601068921.png



aiscot receives AIS Sentences from an AIS Receiver, such as ais-decoder,
converts them to Cursor-on-Target, and transmits the CoT to a UDP destination.

For use with CoT systems such as ATAK, WinTAK, RaptorX,
Falconview, etc. See https://www.civtak.org/ for more information on the TAK
program.

Utilized for an open ocean boat race in the Northern Pacific Ocean, as
described in this article: http://ampledata.org/boat_race_support.html

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


Example Cursor-on-Target Event
==============================

The `aiscot` daemon will output CoT XML Events similar to this example::

    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <event version="2.0" type="a-f-G-E-V-C" uid="AIS.993692014"
        time="2020-09-25T14:15:01.639741Z" start="2020-09-25T14:15:01.639741Z"
        stale="2020-09-25T15:15:01.639741Z" how="h-e">
      <point lat="37.815" lon="-122.78695" hae="10" ce="10" le="10" />
      <detail>
        <uid Droid="6N                  @" />
      </detail>
    </event>



Build Status
============

Master:

.. image:: https://travis-ci.com/ampledata/aiscot.svg?branch=master
    :target: https://travis-ci.com/ampledata/aiscot

Develop:

.. image:: https://travis-ci.com/ampledata/aiscot.svg?branch=develop
    :target: https://travis-ci.com/ampledata/aiscot


Source
======
Github: https://github.com/ampledata/aiscot

Author
======
Greg Albrecht W2GMD oss@undef.net

http://ampledata.org/

Copyright
=========
Copyright 2020 Orion Labs, Inc.

License
=======
Apache License, Version 2.0. See LICENSE for details.

Debugging Cursor-on-Target
==========================
The publicly available ATAK source was a good reference for some of the parsing
errors the ATAK-Civ Development Build was giving me, namely `Invalid CoT
message received: Missing or invalid CoT event and/or point attributes`. Many
errors are unfortunately caught in a single try/catch block:

https://github.com/deptofdefense/AndroidTacticalAssaultKit-CIV/blob/6dc1941f45af3f9716e718dccebf42555a8c08fd/commoncommo/core/impl/cotmessage.cpp#L448

