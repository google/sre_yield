#!/usr/bin/env python3
#
# Copyright 2020 Google Inc.
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

import re
import sys
import unittest

import sre_yield

PY36 = sys.version_info[0:2] == (3, 6)

MAX_REPEAT_COUNT = sre_yield.MAX_REPEAT_COUNT

DOT_STAR_ALL_REPR = "{repeat base=256 low=0 high=%d}" % MAX_REPEAT_COUNT
DOT_STAR_ALL_REPR_ITEM = r"\(%s, (\d+)\)" % DOT_STAR_ALL_REPR


class ReprYieldTest(unittest.TestCase):
    """Test that returned objects have effective repr()."""

    def testDotStar(self):
        parsed = sre_yield.AllStrings(".*", re.DOTALL)
        out = repr(parsed.raw)
        self.assertTrue(re.match(DOT_STAR_ALL_REPR, out))

        parsed = sre_yield.AllStrings(".*.*.*", re.DOTALL)
        out = repr(parsed.raw)

        expected_re = r"{combin \[%s\]}" % ", ".join([DOT_STAR_ALL_REPR_ITEM] * 3)
        self.assertTrue(re.match(expected_re, out))

    def testAlternatives(self):
        parsed = sre_yield.AllStrings(r"a|b")
        self.assertEqual(
            repr(parsed.raw), "{concat [(['a'], 1), (['b'], 1)]}"
        )
        parsed = sre_yield.AllStrings(r"a||b")
        self.assertEqual(
            repr(parsed.raw),
            "{concat [(['a'], 1), (('',), 1), (['b'], 1)]}",
        )

    def testRepeat(self):
        parsed = sre_yield.AllStrings(r"\d{1}")
        self.assertEqual(
            repr(parsed.raw), "{repeat base=10 low=1 high=1}"
        )
        parsed = sre_yield.AllStrings(r"\d{2}")
        self.assertEqual(
            repr(parsed.raw), "{repeat base=10 low=2 high=2}"
        )

    def testRepeatPlus(self):
        parsed = sre_yield.AllStrings(r"\d+")
        out = repr(parsed.raw)

        expected_re = (
            r"{repeat base=10 low=1 high=%d}" % MAX_REPEAT_COUNT
        )
        self.assertTrue(re.match(expected_re, out))

    def testRepeatMulti(self):
        parsed = sre_yield.AllStrings(r"\d{1} \d{1}")
        self.assertEqual(
            repr(parsed.raw),
            "{combin [({repeat base=10 low=1 high=1}, 10), ([' '], 1), ({repeat base=10 low=1 high=1}, 10)]}",
        )

    def testGroup(self):
        parsed = sre_yield.AllStrings(r"(?:\d{2})")
        expected = "{repeat base=10 low=2 high=2}"
        if PY36:
            expected = "{combin [(%s, 100)]}" % expected

        self.assertEqual(repr(parsed.raw), expected)

        parsed = sre_yield.AllStrings(r"(?:\d{,2})")
        expected = "{repeat base=10 low=0 high=2}"
        if PY36:
            expected = "{combin [(%s, 111)]}" % expected

        self.assertEqual(repr(parsed.raw), expected)

    def testBenchInput(self):
        parsed = sre_yield.AllStrings("[01]{,10}")
        self.assertEqual(
            repr(parsed.raw), "{repeat base=2 low=0 high=10}"
        )

        parsed = sre_yield.AllStrings("(?:[a-z]{,10}){,1000}")
        out = repr(parsed.raw)
        expected_re = r"{repeat base=(\d+) low=0 high=1000}"
        m = re.match(expected_re, out)
        self.assertTrue(m)
        self.assertEqual(int(m.group(1)), 146813779479511)

        parsed = sre_yield.AllStrings("(?:[a-z]{,100}){,1000}")
        out = repr(parsed.raw)
        m = re.match(expected_re, out)
        self.assertTrue(m)
        self.assertEqual(
            int(m.group(1)),
            3268647867246256383381332100041691484373976788312974266629140102414955744756908184404049903032490380904202638084876187965749304595652472251351,
        )
        self.assertTrue(re.match(expected_re, out))

    def testBenchInputSlow(self):
        parsed = sre_yield.AllStrings("(?:[a-z]{,100})")
        out = repr(parsed.raw)
        expected_re1 = r"{repeat base=(\d+) low=0 high=100}"
        if PY36:
            expected_re = r"{combin \[\(%s, (\d+)\)\]}" % expected_re1
        else:
            expected_re = expected_re1

        m = re.match(expected_re, out)
        self.assertTrue(m)
        base1 = m.group(1)
        self.assertEqual(int(base1), 26)

        parsed = sre_yield.AllStrings("(?:(?:[a-z]{,100}){,100}){,100}")
        out = repr(parsed.raw)

        if PY36:
            expected_re = expected_re1

        m = re.match(expected_re, out)
        self.assertTrue(m)

        base2 = m.group(1)
        self.assertEqual(len(base2), 14152)

        self.assertGreater(int(base2), int(base1))


if __name__ == "__main__":
    unittest.main()
