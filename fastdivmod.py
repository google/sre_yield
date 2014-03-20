from math import log, ceil
import sys

def genmod(x, by, chunk=None):
  """Generate successive (x % by); x /= by, but faster.

  If provided, |chunk| must be a multiple of |by| (otherwise it is determined
  automatically to match native int size.
  """

  if by == 1:
      assert x == 0, x
      yield 0
      return

  if chunk is None:
      if by > sys.maxint:
          digits_per_chunk = 16
      else:
          digits_per_chunk = int(log(sys.maxint) / log(by))
      chunk = by ** digits_per_chunk
      # only useful with calculated digits_per_chunk
      #if chunk > sys.maxint:
      #    chunk /= by
      #    assert chunk <= sys.maxint, chunk
  else:
      digits_per_chunk = int(round(log(chunk) / log(by)))
      if (by ** digits_per_chunk) != chunk:
        raise ValueError("Chunk=%d must be a power of by=%d" % (chunk, by))

  #print "genmod", chunk, by, digits_per_chunk

  assert digits_per_chunk > 0

  while x:
    x, this_chunk = divmod(x, chunk)
    #this_chunk = int(this_chunk)
    for _ in xrange(digits_per_chunk):
      this_chunk, m = divmod(this_chunk, by)
      yield m

      if this_chunk == 0 and x == 0:
        break


def basic_divmod(x, by, chunk=None):
  # chunk is ignored.
  #print by
  while x:
    x, m = divmod(x, by)
    yield m

def powersum(x, low, high):
  # http://mikestoolbox.com/powersum.html
  xm1 = x - 1
  a = (x ** (high + 1) - 1) / xm1
  b = (x ** low - 1) / xm1
  return a - b

def powersum(x, low, high):
  # http://mikestoolbox.com/powersum.html
  xm1 = x - 1
  if xm1 == 0:
    return high - low + 1
  a = x ** (high + 1)
  b = x ** low
  return (a - b) / xm1
