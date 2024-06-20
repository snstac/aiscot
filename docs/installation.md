AISCOT's functionality provided by a command-line software program called `aiscot`.

## Debian, Ubuntu, Raspberry Pi

Install AISCOT, and prerequisite packages [PyTAK](https://pytak.rtfd.io).

```sh linenums="1"
sudo apt update -qq
wget https://github.com/snstac/pytak/releases/latest/download/pytak_latest_all.deb
sudo apt install -f ./pytak_latest_all.deb
wget https://github.com/snstac/aiscot/releases/latest/download/aiscot_latest_all.deb
sudo apt install -f ./aiscot_latest_all.deb
```

## Windows, Linux

Install from the Python Package Index (PyPI)::

```sh
sudo python3 -m pip install aiscot
```

## Developers

PRs welcome!

```sh linenums="1"
git clone https://github.com/snstac/aiscot.git
cd aiscot/
make editable
```
