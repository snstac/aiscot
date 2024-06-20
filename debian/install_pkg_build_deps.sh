#!/bin/bash

echo "Installing Debian package build dependencies"

apt-get update -qq

apt-get install -y \
  python3 dev pip venv all \
  dh-python debhelper devscripts dput software-properties-common \
  distutils setuptools wheel stdeb
