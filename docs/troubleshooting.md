To report bugs, please set the DEBUG=1 environment variable to collect logs:

```sh
DEBUG=1 aiscot
```

Or:

```sh linenums="1"
export DEBUG=1
aiscot
```

Or:

```sh linenums="1"
echo 'DEBUG=1' >> aiscot.ini
aiscot -c aiscot.ini
```

You can view systemd/systemctl/service logs via:

```journalctl -fu aiscot```

Please use GitHub issues for support requests. Please note that AISCOT is free open source software and comes with no warranty. See LICENSE.

## Database Update

Occasional updates to the YADD Ship Name database can be found at: http://www.yaddnet.org/pages/php/test/tmp/

Updates to the MID database can be found at: TK  
