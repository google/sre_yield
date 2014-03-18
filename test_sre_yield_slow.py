#!/usr/bin/env python2
#
# Copyright 2011-2014 Google Inc.
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

import unittest

import sre_yield

class SlowYieldTest(unittest.TestCase):
    """Test that regular expressions give the right lists."""

    def testDotStarCase(self):
        test_size = sre_yield.Values('.*').__len__()
        actual_size = 0
        for _ in xrange(65536):
            actual_size = actual_size * 256 + 1
        self.assertEquals(test_size, actual_size)


if __name__ == '__main__':
    unittest.main()
