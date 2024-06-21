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

## AISHUB

AISHUB.com requires registration. Once registered the site will provide you with a
Username that you'll use with their feed. You'll also need to specify a Bounding Box 
when accessing the feed. 

The AISHUB_URL must be specified as follows:

``https://data.aishub.net/ws.php?format=1&output=json&compress=0&username=AISHUB_USERNAME&latmin=BBOX_LAT_MIN&latmax=BBOX_LAT_MAX&lonmin=BBOX_LON_MON&lonmax=BBOX_LON_MAX``

Replacing ``AISHUB_USERNAME`` with your AISHUB.com username, and specifying the 
Bounding Box is specified as follows:

* **`latmin`**
    * signed float

    The minimum latitude of the Bounding Box (degrees from Equator) as a signed float (use negative sign for East: ``-``).

* **`latmax`**
    * signed float

    The maximum latitude of the Bounding Box (degrees from Equator) as a signed float (use negative sign for East: ``-``).

* **`lonmin`**
    * signed float
    
    The minimum longitude of the Bound Box (degrees from Prime Meridian) as a signed float (use negative sign for North: ``-``).

* **`lonmax`**
    * signed float
    
    The maximum longitude of the Bound Box (degrees from Prime Meridian) as a signed float (use negative sign for North: ``-``).

For example, the following Bound Box paints a large swath around Northern California: 
``latmin=35&latmax=38&lonmin=-124&lonmax=-121``. This can be read as: 
"Between 35° and 38° latitude & -121° and -124° longitude".

## Run as a service / Run forever

1. Add the text contents below a file named `/lib/systemd/system/aiscot.service`  
  You can use `nano` or `vi` editors: `sudo nano /lib/systemd/system/aiscot.service`
2. Reload systemctl: `sudo systemctl daemon-reload`
3. Enable AISCOT: `sudo systemctl enable aiscot`
4. Start AISCOT: `sudo systemctl start aiscot`

```ini
{!debian/aiscot.service!}
```


> Pay special attention to the `ExecStart` line above. You'll need to provide the full local filesystem path to both your `aiscot` executable & AISCOT configuration files.