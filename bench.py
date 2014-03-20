#!/usr/bin/env python2

import copy
import os
import sys
import time

sys.path.insert(0, os.getcwd())

import sre_yield

def first_slice(obj):
  for i in xrange(10):
    x = obj[i]
    del x

def last_slice(obj):
  for i in xrange(10):
    x = obj[-(i+1)]
    del x

def index(n):
  def inner(obj):
    x = obj[n]
    del x
  return inner

def main(args):
  pattern = args[0]
  min_time = 1.0

  sys.stdout.write("%s\t" % (pattern,)); sys.stdout.flush()
  path = sre_yield.__file__
  if '/' not in path:
    path = os.getcwd()
  path = os.path.dirname(path)

  if path.endswith('_vanilla'):
    sys.stdout.write("old\t"); sys.stdout.flush()
  elif path.endswith('_thatch'):
    sys.stdout.write("new\t"); sys.stdout.flush()
  else:
    raise ValueError("Unknown path", path)


  t0 = time.time()
  v = sre_yield.Values(pattern)
  t1 = time.time()

  sys.stdout.write("%.05f\t" % (t1-t0,)); sys.stdout.flush()

  for test in (index(0), index(1), index(-2), index(-1), first_slice, last_slice):
    v2 = sre_yield.Values(pattern)
    t0 = time.time()
    iterations = 0
    delta = 0
    first_delta = None
    while delta < min_time:
      test(v2)
      if isinstance(delta, int):
        first_delta = time.time() - t0
        sys.stdout.write("%.05f\t" % (first_delta,)); sys.stdout.flush()

      iterations += 1
      delta = time.time() - t0

    sys.stdout.write("%.05f\t" % (delta / iterations,)); sys.stdout.flush()

  with open('/proc/self/status') as f:
    for line in f:
      if line.startswith('VmPeak'):
        print line.split(':')[1].strip().rstrip(' kB')
        return
    else:
      print

if __name__ == '__main__':
  main(sys.argv[1:])
