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
      digits_per_chunk = int(log(sys.maxint) / log(by))
      chunk = by ** digits_per_chunk
      if chunk > sys.maxint:
          chunk /= by
          assert chunk <= sys.maxint, chunk
  else:
      digits_per_chunk = int(round(log(chunk) / log(by)))
      if (by ** digits_per_chunk) != chunk:
        raise ValueError("Chunk=%d must be a power of by=%d" % (chunk, by))

  #print chunk, by, digits_per_chunk

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
