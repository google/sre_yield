import sys
import random
import itertools
import unittest
from fastdivmod import genmod, basic_divmod

class FastDivmodTest(unittest.TestCase):
  def test_basic_divmod(self):
    v = basic_divmod(1234, 10)
    self.assertEquals([4, 3, 2, 1], list(v))

  def test_basics(self):
    v = genmod(1234, 10, 10)
    self.assertEquals([4, 3, 2, 1], list(v))

    v = genmod(1234, 10, 100)
    self.assertEquals([4, 3, 2, 1], list(v))

    v = genmod(1234, 10, 1000)
    self.assertEquals([4, 3, 2, 1], list(v))

  def test_bad_chunk_sizes(self):
    g = genmod(1234, 10, 11)
    self.assertRaises(ValueError, g.next)

  def test_huge_number_1(self):
    v = genmod(70110209207109374, 255)
    self.assertEquals([254, 254, 254, 254, 254, 254, 254], list(v))

  def test_huge_number_2(self):
    bignum = 1162523670191533212890624

    assert 255**11 > bignum
    v = genmod(bignum, 255, 255**11)
    self.assertEquals([254, 254, 254, 254, 254, 254, 254, 254, 254, 254], map(int, v))

    assert 255**9 < bignum
    v = genmod(bignum, 255, 255**9)
    self.assertEquals([254, 254, 254, 254, 254, 254, 254, 254, 254, 254], map(int, v))

def test_correctness_big_numbers():
  random.seed(1)
  for _ in range(100):
    x = random.randint(1, 2**32)
    for base in (2, 10, 255, 256):
      for chunk in (base, base**2, base**3, base**4):
        yield runner, x, base, chunk

  for _ in range(10):
    x = random.randint(1, 2**32) * sys.maxint ** 6
    for base in (2, 10, 255, 256):
      for chunk in (base, base**2, base**3, base**4):
        yield runner, x, base, chunk

def runner(x, base, chunk):
  for i, j in itertools.izip_longest(genmod(x, base, chunk), basic_divmod(x, base)):
    if i is None:
      print "phooey"
    else:
      assert i == j
