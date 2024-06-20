# Concept of Operations

AISCOT can operate in two different modes, as described in detail below:

1. AIS Over-the-air (RF)
2. AIS Aggregator (AISHUB)

## AIS Over-the-air Operation (RF)

![AISCOT "AIS Over the Air" CONOP](aiscot_ota.png)

Receive AIS data from a VHF AIS receiver, such as the 
Megwatt `dAISy+ <https://shop.wegmatt.com/products/daisy-ais-receiver>`_. From there 
AIS can be decoded by `AIS Dispatcher <https://www.aishub.net/ais-dispatcher>`_ and 
forwarded to AISCOT to be transformed to COT and transmitted to COT destinations.

## AIS Aggregator Operation (AISHUB.com)

![AISCOT "AIS Aggregator" CONOP](aiscot_agg.png)
   
Receive AIS data from the `AISHUB <https://www.aishub.com>`_ service. 
Requires a subscription to AISHUB.
