#!/usr/bin/env python3
#
# Copyright 2011-2016 Google Inc.
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
#
# vim: sw=2 sts=2 et

import copy
import os
import sys
import time

t = os.path.dirname(sys.argv[0])
root = os.path.abspath(os.path.join(t, ".."))
sys.path.insert(0, root)

if True:
    import sre_yield  # isort:skip didn't seem to work


def first_slice(obj):
    for i in range(10):
        x = obj[i]
        del x


def last_slice(obj):
    for i in range(10):
        x = obj[-(i + 1)]
        del x


def index(n):
    def inner(obj):
        x = obj[n]
        del x

    return inner


def main(args):
    pattern = args[0]
    sys.stdout.write("%s\t" % (pattern,))
    sys.stdout.flush()

    name = args[1]

    sys.stdout.write("%s\t" % (name,))
    sys.stdout.flush()

    min_time = 1.0

    t0 = time.time()
    v = sre_yield.Values(pattern)
    t1 = time.time()

    sys.stdout.write("%.05f\t" % (t1 - t0,))
    sys.stdout.flush()

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
                sys.stdout.write("%.05f\t" % (first_delta,))
                sys.stdout.flush()

            iterations += 1
            delta = time.time() - t0

        sys.stdout.write("%.05f\t" % (delta / iterations,))
        sys.stdout.flush()

    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmPeak"):
                print(line.split(":")[1].strip().rstrip(" kB"))
                return
        else:
            print()


if __name__ == "__main__":
    main(sys.argv[1:])
