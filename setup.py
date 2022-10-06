#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Greg Albrecht <oss@undef.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author:: Greg Albrecht W2GMD <oss@undef.net>
#

"""
Setup for the AIS Cursor-On-Target Gateway.

Source:: https://github.com/ampledata/aiscot
"""

import os
import sys

import setuptools

__title__ = "aiscot"
__version__ = "5.1.0"
__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


def publish():
    """Function for publishing package to pypi."""
    if sys.argv[-1] == "publish":
        os.system("python setup.py sdist")
        os.system("twine upload dist/*")
        sys.exit()


publish()


def read_readme(readme_file="README.rst") -> str:
    """Read the contents of the README file for use as a long_description."""
    readme: str = ""
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_directory, readme_file), encoding="utf-8") as frm:
        readme = frm.read()
    return readme


setuptools.setup(
    version=__version__,
    name=__title__,
    packages=[__title__],
    package_dir={__title__: __title__},
    url=f"https://github.com/ampledata/{__title__}",
    entry_points={"console_scripts": [f"{__title__} = {__title__}.commands:main"]},
    description="AIS Cursor-On-Target Gateway.",
    author="Greg Albrecht",
    author_email="oss@undef.net",
    package_data={"": ["LICENSE"]},
    license="Apache License, Version 2.0",
    long_description=read_readme(),
    long_description_content_type="text/x-rst",
    zip_safe=False,
    include_package_data=True,
    install_requires=["pytak >= 5.4.0", "aiohttp"],
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
    ],
    keywords=["Sailing", "AIS", "Cursor on Target", "ATAK", "TAK", "CoT"],
)
