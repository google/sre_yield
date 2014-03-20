from math import log, ceil
import sys

def genmod(x, by, chunk=None):
  """Generate successive (x % by); x /= by, but faster.

  If provided, |chunk| must be a multiple of |by| (otherwise it is determined
  automatically to match native int size.
  """

  if chunk is None:
    chunk = sys.maxint - sys.maxint % by

  if chunk % by != 0:
    raise ValueError("Chunk %d must be a multiple of by %d" % (chunk, by))

  inner_count = int(ceil(log(chunk) / log(by)))
  print chunk, by, inner_count

  while x:
    x, this_chunk = divmod(x, chunk)
    #this_chunk = int(this_chunk)
    for _ in xrange(inner_count):
      this_chunk, m = divmod(this_chunk, by)
      yield m

      if this_chunk == 0 and x == 0:
        break


def basic_divmod(x, by, chunk=None):
  # chunk is ignored.
  print by
  while x:
    x, m = divmod(x, by)
    yield m
