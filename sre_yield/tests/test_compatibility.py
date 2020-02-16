import itertools
import re
import unittest
from typing import List, Optional, Pattern

import sre_yield
from sre_yield.testing_utils import UnitTest, data_provider


def match_list(pattern: Pattern, max_length: int, charset: str) -> List[str]:
    # Given a compiled pattern, finds the strings of <= max_length that
    # fullmatch it.
    r = []
    for i in range(max_length + 1):
        for p in itertools.product(*([charset] * i)):
            ps = "".join(p)
            if pattern.fullmatch(ps):
                r.append(ps)

    return r


class MatchListTest(UnitTest):
    @data_provider(
        (
            # Don't want black to wrap this block.
            (0, [""]),
            (1, ["", "0", "1"]),
            (2, ["", "0", "1", "00", "01", "10", "11"]),
        )
    )
    def test_match_list(self, count, expected):
        el = match_list(re.compile(".*"), count, "01")
        self.assertEqual(expected, el)


class CompatibilityTest(UnitTest):
    def _verify(
        self,
        pat: str,
        max_length: int,
        expected_failure: bool = False,
        m: Optional[List[str]] = None,
    ):
        # If this changes, some examples will need to be updated, especially
        # when thinning is implemented for charclasses.
        # See https://github.com/google/sre_yield/issues/2
        charset = "-abc"
        pat_re = re.compile(pat)
        expected = match_list(pat_re, max_length=max_length, charset=charset)

        # TODO currently sorts because some examples like '..' or '[ab][ab]' are
        # not in the order we get from match_list
        actual = sorted(
            [
                x
                for x in sre_yield.AllStrings(
                    pat, charset=charset, max_count=max_length
                )
                if len(x) <= max_length
            ],
            key=lambda i: (len(i), i),
        )

        # These document current behavior, even when it's wrong, and when they
        # start passing we want to know.
        if expected_failure:
            self.assertNotEqual(expected, actual)
        else:
            self.assertEqual(
                expected,
                actual,
                f"\n\nfor pattern {pat!r} of <={max_length}\n"
                f">  expected={expected}\n> sre_yield={actual}",
            )

            if m is not None:
                self.assertEqual(
                    m,
                    actual,
                    f"\n\nfor pattern {pat!r} of <={max_length}\n"
                    f">         m={m}\n> sre_yield={actual}",
                )

    @data_provider(
        (
            {"pat": r".", "max_length": 1},
            {"pat": r"..", "max_length": 2},
            {"pat": r".{,3}", "max_length": 3},
            {"pat": r".*", "max_length": 3},
        )
    )
    def test_repeat(self, pat: str, max_length: int) -> None:
        self._verify(pat, max_length)

    @data_provider(
        (
            {"pat": r"[a].", "max_length": 2},
            {"pat": r"[ac].", "max_length": 2},
            {"pat": r"[^ac].", "max_length": 2},
        )
    )
    def test_charclass(self, pat: str, max_length: int) -> None:
        self._verify(pat, max_length)

    @data_provider(
        (
            {"pat": r"^a$", "max_length": 1},
            {"pat": r"^\ba\b$", "max_length": 1},
            {"pat": r"^^^\b\ba\b\b\b$$$", "max_length": 1},
        )
    )
    def test_anchors(self, pat: str, max_length: int) -> None:
        self._verify(pat, max_length)


if __name__ == "__main__":
    unittest.main()
