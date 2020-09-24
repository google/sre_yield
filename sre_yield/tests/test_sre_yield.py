#!/usr/bin/env python3
#
# Copyright 2011-2016 Google Inc.
# Copyright 2018-2019 Tim Hatch
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

import io
import re
import sre_parse
import sys
import unittest

import sre_yield

PY36 = sys.version_info[0:2] == (3, 6)


class YieldTest(unittest.TestCase):
    """Test that regular expressions give the right lists."""

    def testSimpleCases(self):
        self.assertSequenceEqual(
            sre_yield.AllStrings("1(234?|49?)"), ["123", "1234", "14", "149"]
        )
        self.assertSequenceEqual(sre_yield.AllStrings("asd|def"), ["asd", "def"])
        self.assertSequenceEqual(
            sre_yield.AllStrings("asd|def\\+|a\\.b\\.c"), ["asd", "def+", "a.b.c"]
        )

    def testOtherCases(self):
        self.assertSequenceEqual(sre_yield.AllStrings("[aeiou]"), list("aeiou"))
        self.assertEqual(len(sre_yield.AllStrings("1.3", flags=re.DOTALL)), 256)
        v = sre_yield.AllStrings("[^-]3[._]1415", flags=re.DOTALL)
        self.assertEqual(len(v), 510)
        self.assertEqual(
            len(sre_yield.AllStrings("(.|5[6-9]|[6-9][0-9])[a-z].?", flags=re.DOTALL)),
            300 * 26 * 257,
        )
        self.assertEqual(len(sre_yield.AllStrings("..", charset="0123456789")), 100)
        self.assertEqual(len(sre_yield.AllStrings("0*")), 65536)
        self.assertEqual(sre_yield.AllStrings("[01]*").__len__(), 2 ** 65536 - 1)

    def testOverflowError(self):
        # For really big lists, we can't use the len() function any more
        with self.assertRaises(OverflowError) as cm:
            len(sre_yield.AllStrings(r"\d+"))
        self.assertEqual(
            str(cm.exception), "cannot fit 'int' into an index-sized integer"
        )

        with self.assertRaises(OverflowError) as cm:
            len(sre_yield.AllStrings("[01]*"))
        self.assertEqual(
            str(cm.exception), "cannot fit 'int' into an index-sized integer"
        )

    def testLargeSequenceSliceLength(self):
        self.assertEqual(len(sre_yield.AllStrings(r"\d+")[:16]), 16)
        self.assertEqual(len(sre_yield.AllStrings(r"(\d+){1}")[:16]), 16)
        self.assertEqual(len(sre_yield.AllStrings(r"([\d]+){1}")[:16]), 16)
        self.assertEqual(len(sre_yield.AllStrings(r"([\d]+)?")[:16]), 16)
        self.assertEqual(len(sre_yield.AllStrings(r"([\d]*){1}")[:16]), 16)
        self.assertEqual(len(sre_yield.AllStrings(r"\d+", max_count=1)[:16]), 10)

    def testAlternationWithEmptyElement(self):
        self.assertSequenceEqual(sre_yield.AllStrings("a(b|c|)"), ["ab", "ac", "a"])
        self.assertSequenceEqual(sre_yield.AllStrings("a(|b|c)"), ["a", "ab", "ac"])
        self.assertSequenceEqual(sre_yield.AllStrings("a[bc]?"), ["a", "ab", "ac"])
        self.assertSequenceEqual(sre_yield.AllStrings("a[bc]??"), ["a", "ab", "ac"])

    def testSlices(self):
        parsed = sre_yield.AllStrings("[abcdef]")
        self.assertSequenceEqual(parsed[::2], list("ace"))
        self.assertSequenceEqual(parsed[1::2], list("bdf"))
        self.assertSequenceEqual(parsed[1:-1], list("bcde"))
        self.assertSequenceEqual(parsed[1:-2], list("bcd"))
        self.assertSequenceEqual(parsed[1:99], list("bcdef"))

        self.assertSequenceEqual(parsed[0:0], [])
        self.assertSequenceEqual(parsed[1:1], [])
        self.assertSequenceEqual(parsed[-1:-99], [])
        self.assertSequenceEqual(parsed[99:], [])
        self.assertSequenceEqual(parsed[:-99], [])
        self.assertSequenceEqual(parsed[99:-99], [])

    def testSliceReverse(self):
        parsed = sre_yield.AllStrings("[abcdef]")
        self.assertSequenceEqual(parsed[::-1], list("fedcba"))
        self.assertSequenceEqual(parsed[::-2], list("fdb"))

        self.assertSequenceEqual(parsed[99::-1], list("fedcba"))
        self.assertSequenceEqual(parsed[99:-99:-1], list("fedcba"))

        self.assertSequenceEqual(parsed[99::-2], list("fdb"))
        self.assertSequenceEqual(parsed[99:-99:-2], list("fdb"))

        self.assertSequenceEqual(parsed[::-99], ["f"])
        self.assertSequenceEqual(parsed[99::-99], ["f"])
        self.assertSequenceEqual(parsed[99:-99:-99], ["f"])

    def testSliceStepZero(self):
        parsed = sre_yield.AllStrings("[abcdef]")
        with self.assertRaises(ValueError) as cm:
            parsed[0:1:0]
        self.assertEqual(str(cm.exception), "slice step cannot be zero")

    def testSlicesRepeated(self):
        parsed = sre_yield.AllStrings("[abcdef]")
        self.assertSequenceEqual(parsed[::-1][:2], list("fe"))
        self.assertSequenceEqual(parsed[1:][1:][1:-1], list("de"))
        self.assertSequenceEqual(parsed[::2][1:], list("ce"))

    def testGetItemNegative(self):
        parsed = sre_yield.AllStrings("x|[a-z]{1,5}")
        self.assertEqual(parsed[0], "x")
        self.assertEqual(parsed[1], "a")
        self.assertEqual(parsed[23], "w")
        self.assertEqual(parsed[24], "x")
        self.assertEqual(parsed[25], "y")
        self.assertEqual(parsed[26], "z")
        self.assertEqual(parsed[27], "aa")
        self.assertEqual(parsed[28], "ab")
        self.assertEqual(parsed[-2], "zzzzy")
        self.assertEqual(parsed[-1], "zzzzz")

        # last, and first
        parsed.get_item(len(parsed) - 1)
        parsed.get_item(-len(parsed))

    def testGetItemNegativeIndexError(self):
        parsed = sre_yield.AllStrings("x|[a-z]{1,5}")
        # precisely 1 out of bounds
        with self.assertRaises(IndexError) as cm:
            parsed.get_item(len(parsed))
        self.assertEqual(str(cm.exception), "Index %d out of bounds" % len(parsed))

        with self.assertRaises(IndexError) as cm:
            parsed.get_item(-len(parsed) - 1)
        self.assertEqual(
            str(cm.exception), "Index %d out of bounds" % (-len(parsed) - 1)
        )

    def testIndexError(self):
        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("x").get_item(1)
        self.assertEqual(str(cm.exception), "Index 1 out of bounds")

        with self.assertRaises(IndexError) as cm:
            parsed = sre_yield.AllStrings("xa{3}[a]y")
            print(list(parsed))
            parsed.get_item(1)
        self.assertEqual(str(cm.exception), "Index 1 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("x?").get_item(2)
        self.assertEqual(str(cm.exception), "Index 2 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("[xy]").get_item(2)
        self.assertEqual(str(cm.exception), "Index 2 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("x|y").get_item(2)
        self.assertEqual(str(cm.exception), "Index 2 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("xa?y").get_item(2)
        self.assertEqual(str(cm.exception), "Index 2 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings(r"x\dy").get_item(10)
        self.assertEqual(str(cm.exception), "Index 10 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("x").get_item(-2)
        self.assertEqual(str(cm.exception), "Index -2 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("xa{3}[a]y").get_item(-2)
        self.assertEqual(str(cm.exception), "Index -2 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("[xy]").get_item(-3)
        self.assertEqual(str(cm.exception), "Index -3 out of bounds")

        with self.assertRaises(IndexError) as cm:
            sre_yield.AllStrings("x|y").get_item(-3)
        self.assertEqual(str(cm.exception), "Index -3 out of bounds")

    def testUnsupportedErrors(self):
        parsed = sre_yield.AllStrings("x")
        self.assertSequenceEqual(parsed, ["x"])
        with self.assertRaises(TypeError) as cm:
            parsed[:] = ["a"]
        self.assertEqual(
            str(cm.exception),
            "'RegexMembershipSequence' object does not support item assignment",
        )

        with self.assertRaises(TypeError) as cm:
            del parsed[0]
        self.assertEqual(
            str(cm.exception),
            "'RegexMembershipSequence' object doesn't support item deletion",
        )

    def testContains(self):
        parsed = sre_yield.AllStrings("[01]+")
        self.assertTrue("0101" in parsed)
        self.assertFalse("0201" in parsed)

    def testPreparsedInstantiation(self):
        self.assertSequenceEqual(sre_yield.AllStrings(r"(?:[aeiou])\Z"), list("aeiou"))
        preparsed = sre_parse.parse("[aeiou]")
        self.assertSequenceEqual(sre_yield.AllStrings(preparsed), list("aeiou"))
        preparsed = sre_parse.parse(r"(?:[aeiou])\Z")
        self.assertSequenceEqual(sre_yield.AllStrings(preparsed), list("aeiou"))

        preparsed = sre_parse.parse("[01]+")
        parsed = sre_yield.AllStrings(preparsed)
        self.assertTrue("0101" in parsed)
        self.assertFalse("0201" in parsed)

        preparsed = sre_parse.parse("[01]+")
        parsed = sre_yield.AllStrings(preparsed)
        self.assertTrue("0101" in parsed)
        self.assertFalse("0201" in parsed)

        preparsed = sre_parse.parse(r"(?:[01]+)\Z")
        parsed = sre_yield.AllStrings(preparsed)
        self.assertTrue("0101" in parsed)
        self.assertFalse("0201" in parsed)

    def testNaturalOrder(self):
        parsed = sre_yield.AllStrings("[0-9]{2}")
        self.assertEqual(parsed[0], "00")
        self.assertEqual(parsed[1], "01")
        self.assertEqual(parsed[98], "98")
        self.assertEqual(parsed[99], "99")

    def testCategories(self):
        cat_chars = "wWdDsS"
        for c in cat_chars:
            r = re.compile("\\" + c, flags=sre_yield.DEFAULT_RE_FLAGS)
            matching = [i for i in sre_yield.CHARSET if r.match(i)]
            self.assertGreater(len(matching), 5)
            parsed = sre_yield.AllStrings("\\" + c)
            self.assertEqual(sorted(matching), sorted(parsed[:]))

    def testDotallFlag(self):
        parsed = sre_yield.AllStrings(".", charset="abc\n")
        self.assertEqual(["a", "b", "c"], parsed[:])
        parsed = sre_yield.AllStrings(".", charset="abc\n", flags=re.DOTALL)
        self.assertEqual(["a", "b", "c", "\n"], parsed[:])

    def testMaxCount(self):
        parsed = sre_yield.AllStrings("[01]+", max_count=4)
        self.assertEqual("1111", parsed[-1])

    def testMinCount(self):
        parsed = sre_yield.AllStrings(r"\d{0}")
        self.assertEqual([""], list(parsed))
        parsed = sre_yield.AllStrings(r"\d{2}")
        self.assertEqual("99", parsed[-1])
        parsed = sre_yield.AllStrings(r"\d{2}", max_count=1)
        self.assertEqual("99", parsed[-1])

    def testParseErrors(self):
        self.assertRaises(sre_yield.ParseError, sre_yield.AllStrings, "a", re.I)
        self.assertRaises(sre_yield.ParseError, sre_yield.AllStrings, "a", re.U)
        # Causes a failure inside sre_parse under Python 3.6
        with self.assertRaises(ValueError) as cm:
            sre_yield.AllStrings("a", re.L)
        self.assertEqual(str(cm.exception), "cannot use LOCALE flag with a str pattern")

    def testSavingGroups(self):
        parsed = sre_yield.AllStrings(r"(([abc])d)e")
        d = {}
        self.assertEqual("ade", parsed.get_item(0, d))
        self.assertEqual("ad", d[1])
        self.assertEqual("a", d[2])

    def testSavingGroupsByName(self):
        parsed = sre_yield.AllMatches(r"x(?P<foo>[abc])x")
        m = parsed[0]
        self.assertEqual("xax", m.group(0))
        self.assertEqual("a", m.group(1))
        self.assertEqual("a", m.group("foo"))
        self.assertEqual({"foo": "a"}, m.groupdict())
        self.assertRaises(NotImplementedError, m.span)

    def testBackrefCounts(self):
        parsed = sre_yield.AllStrings(r"([abc])-\1")
        self.assertEqual(3, len(parsed))
        self.assertEqual(["a-a", "b-b", "c-c"], parsed[:])

    def testSlicingMatches(self):
        parsed = sre_yield.AllMatches(r"([abcd])-\1")
        self.assertEqual(4, len(parsed))
        self.assertEqual(4, len(parsed[:]))
        self.assertTrue(all(isinstance(item, str) for item in parsed))
        self.assertTrue(all(isinstance(item, sre_yield.Match) for item in parsed[:]))
        self.assertEqual(["a-a", "b-b", "c-c", "d-d"], [x for x in parsed])
        self.assertEqual(["a-a", "b-b"], [x.group(0) for x in parsed[:2]])
        self.assertEqual(["a", "b"], [x.group(1) for x in parsed[:2]])

    def testSlicingMatchesMultichar(self):
        parsed = sre_yield.AllMatches("z([ab]{2})")
        self.assertEqual(4, len(parsed))
        self.assertEqual(4, len(parsed[:]))
        self.assertTrue(all(isinstance(item, str) for item in parsed))
        self.assertTrue(all(isinstance(item, sre_yield.Match) for item in parsed[:]))
        self.assertEqual(["zaa", "zab", "zba", "zbb"], [x for x in parsed])
        self.assertEqual(["zaa", "zab", "zba", "zbb"], [x.group(0) for x in parsed[:]])
        self.assertEqual(["aa", "ab", "ba", "bb"], [x.group(1) for x in parsed[:]])

        parsed = sre_yield.AllMatches("([ab]{2})")
        self.assertEqual(4, len(parsed))
        self.assertEqual(4, len(parsed[:]))
        self.assertTrue(all(isinstance(item, str) for item in parsed))
        self.assertTrue(all(isinstance(item, sre_yield.Match) for item in parsed[:]))
        self.assertEqual(["aa", "ab", "ba", "bb"], [x for x in parsed])
        self.assertEqual(["aa", "ab", "ba", "bb"], [x.group(0) for x in parsed[:]])
        self.assertEqual(["aa", "ab", "ba", "bb"], [x.group(1) for x in parsed[:]])

    def testAllStringsIsValues(self):
        self.assertEqual(sre_yield.AllStrings, sre_yield.Values)

    def testCanIterateGiantValues(self):
        v = sre_yield.AllStrings(".+")
        self.assertGreater(v.__len__(), sys.maxsize)
        it = iter(v)
        self.assertEqual("\x00", next(it))
        self.assertEqual("\x01", next(it))

    def testCanSliceGiantValues(self):
        v = sre_yield.AllStrings(".+")
        self.assertGreater(v.__len__(), sys.maxsize)
        self.assertEqual(["\x00", "\x01"], list(v[:2]))

    def testOffset(self):
        # This was discovered after https://github.com/google/sre_yield/issues/10
        v = sre_yield.AllStrings("([0-9a-fA-F]{0,4}:){0,5}")
        el = v.__len__()
        self.assertTrue(v.__getitem__(el - 1))

    def testMain(self):
        old_sys_stdout = sys.stdout

        buf = io.StringIO()
        try:
            sys.stdout = buf
            sre_yield.main(["prog", "x[123]"])
        finally:
            sys.stdout = old_sys_stdout

        self.assertEqual("x1\nx2\nx3\n", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
