#!/usr/bin/env python2
#
# Copyright 2011-2016 Google Inc.
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
#
# vim: sw=2 sts=2 et

from setuptools import setup, find_packages
import os.path

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

version = '1.0'

setup(name='sre_yield',
      version=version,
      description='Expands a regular expression to its possible matches',
      long_description=README,
      classifiers = [
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
      ],
      keywords='',
      author='Alex Perry',
      author_email='alex.perry@google.com',
      url='https://github.com/google/sre_yield',
      license='Apache',
      packages=find_packages('.'),
      install_requires=[],
      entry_points={
        'console_scripts': [
            'demo_sre_yield=sre_yield:main',
        ],
      },
      test_suite='nose.collector', # doesn't find doctests though
      tests_require=['nose'],
)
