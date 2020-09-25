#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup for the AIS Cursor-on-Target Gateway.

Source:: https://github.com/ampledata/aiscot
"""

import os
import sys

import setuptools

__title__ = 'aiscot'
__version__ = '1.0.0'
__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def publish():
    """Function for publishing package to pypi."""
    if sys.argv[-1] == 'publish':
        os.system('python setup.py sdist')
        os.system('twine upload dist/*')
        sys.exit()


publish()


setuptools.setup(
    name=__title__,
    version=__version__,
    description='AIS Cursor-on-Target Gateway.',
    author='Greg Albrecht',
    author_email='oss@undef.net',
    packages=['aiscot'],
    package_data={'': ['LICENSE']},
    package_dir={'aiscot': 'aiscot'},
    license=open('LICENSE').read(),
    long_description=open('README.rst').read(),
    url='https://github.com/ampledata/aiscot',
    zip_safe=False,
    include_package_data=True,
    setup_requires=[
        'coverage >= 3.7.1',
        'httpretty >= 0.8.10',
        'pytest'
    ],
    install_requires=[
        'libais >= 0.16',
        'pycot >= 2.0.0',
        'gexml'
    ],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache Software License'
    ],
    keywords=[
        'Sailing', 'AIS', 'Cursor on Target', 'ATAK', 'TAK', 'CoT'
    ],
    entry_points={'console_scripts': ['aiscot = aiscot.cmd:cli']}
)
