#!/usr/bin/env python3
#
# Copyright 2011-2016 Google Inc.
# Copyright 2018-2020 Tim Hatch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path

from setuptools import find_packages, setup

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(THIS_DIR, "README.rst")).read()

VERSION = "1.3"

setup(
    name="sre_yield",
    version=VERSION,
    description="Expands a regular expression to its possible matches",
    long_description=README,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
    ],
    keywords="",
    author="Alex Perry",
    author_email="alex.perry@google.com",
    url="https://github.com/google/sre_yield",
    license="Apache",
    packages=find_packages("."),
    install_requires=[],
    entry_points={"console_scripts": ["demo_sre_yield=sre_yield:main"]},
    requires_python=">=3.6",
)
