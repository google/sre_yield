import unittest
import cachingseq

class CachingFuncSequenceTest(unittest.TestCase):
  def testLimits(self):
    c = cachingseq.CachingFuncSequence(lambda i: i, 10)
    self.assertEquals(9, c[9])
    self.assertEquals(9, c[-1])
    self.assertEquals(0, c[0])
    self.assertEquals(0, c[-10])
    self.assertRaises(IndexError, lambda: c[10])
    self.assertRaises(IndexError, lambda: c[11])
    self.assertRaises(IndexError, lambda: c[-11])
    self.assertRaises(IndexError, lambda: c[-12])
    self.assertEquals(2, len(c._cache))

    # Make sure .func is settable at runtime...
    c.func = lambda i: 'bbb'
    self.assertEquals('bbb', c[1])
    # ...and that we don't call it again.
    self.assertEquals(0, c[0])

  def testIter(self):
    c = cachingseq.CachingFuncSequence(lambda i: i, 10)
    # Cache empty on construction
    self.assertEquals(0, len(c._cache))

    self.assertEquals(10, len(c))
    self.assertEquals(range(10), list(c))

    # Cache full after iteration
    self.assertEquals(10, len(c._cache))

  def testIncFunc(self):
    def first_func(x):
      assert x == 0
      return 1

    def inc_func(i, prev):
      return prev * 2

    c = cachingseq.CachingFuncSequence(first_func, 10, inc_func)
    self.assertEquals([1, 2, 4, 8, 16, 32, 64, 128, 256, 512], list(c))
