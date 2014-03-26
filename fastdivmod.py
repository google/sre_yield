from math import log, ceil
import sys


def find_largest_power(less_than, base):
    power = int(log(less_than) / log(base))
    return base ** power


def divmod_iter(x, by, chunk=None):
  if x < by:
    return [x]

  if hasattr(x, 'bit_length'):
    # crude log(2, x)
    divisions = x.bit_length() / by.bit_length()
  else:
    divisions = log(x) / log(by)

  if divisions < 1024:
    return divmod_iter_basic(x, by, chunk)
  else:
    return divmod_iter_chunking(x, by, chunk)


def divmod_iter_chunking(x, by, chunk=None):
  """Generate successive (x % by); x /= by, but faster.

  If provided, |chunk| must be a power of |by| (otherwise it is determined
  automatically for 1024 per inner loop, based on analysis of bench_genmod.py)
  """

  if by == 1:
      assert x == 0, x
      yield 0
      return

  if chunk is None:
      digits_per_chunk = 1024
      chunk = by ** digits_per_chunk
  else:
      digits_per_chunk = int(round(log(chunk) / log(by)))
      if (by ** digits_per_chunk) != chunk:
        raise ValueError("Chunk=%d must be a power of by=%d" % (chunk, by))

  assert digits_per_chunk > 0

  while x:
    x, this_chunk = divmod(x, chunk)
    #this_chunk = int(this_chunk)
    for _ in xrange(digits_per_chunk):
      this_chunk, m = divmod(this_chunk, by)
      yield m

      if this_chunk == 0 and x == 0:
        break


def divmod_iter_basic(x, by, chunk=None):
  """Generate successive (x % by); x /= by, the obvious way.

  Chunk is ignored.
  """
  while x:
    x, m = divmod(x, by)
    yield m

def powersum(x, low, high):
  # http://mikestoolbox.com/powersum.html
  xm1 = x - 1
  if xm1 == 0:
    return high - low + 1
  a = x ** (high + 1)
  b = x ** low
  return (a - b) / xm1
