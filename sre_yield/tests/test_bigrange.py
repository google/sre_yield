#!/usr/bin/env python3
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

import sys
import unittest

import sre_yield
from sre_yield.testing_utils import UnitTest, data_provider

# fmt: off
TESTCASES = [
    (5,),
    (1, 5),
    (1, 5, 1),
    (1, 10, 2),
    (10, 1, -1),
    (10, -1, -1),
]
# fmt: on


class BigRangeTest(UnitTest):
    @data_provider([(x,) for x in TESTCASES])
    def test_all(self, packed_test):
        expected = list(range(*packed_test))
        actual = list(sre_yield._bigrange(*packed_test))
        self.assertEqual(expected, actual)

    def test_bignum(self):
        # xrange(start, stop) raises OverflowError in py2.7
        start = sys.maxsize
        stop = sys.maxsize + 5

        el = list(sre_yield._bigrange(start, stop))
        self.assertEqual(5, len(el))


if __name__ == "__main__":
    unittest.main()
