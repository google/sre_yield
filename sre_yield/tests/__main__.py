import unittest

from sre_yield.tests.test_anchors import AnchorTest  # noqa: F401
from sre_yield.tests.test_bigrange import BigRangeTest  # noqa: F401
from sre_yield.tests.test_cachingseq import CachingFuncSequenceTest  # noqa: F401
from sre_yield.tests.test_compatibility import (  # noqa: F401
    CompatibilityTest,
    MatchListTest,
)
from sre_yield.tests.test_fastdivmod import FastDivmodTest  # noqa: F401
from sre_yield.tests.test_slicing import SlicingTest  # noqa: F401
from sre_yield.tests.test_sre_yield import YieldTest  # noqa: F401
from sre_yield.tests.test_sre_yield_slow import SlowYieldTest  # noqa: F401

unittest.main()
