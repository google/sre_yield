#!/usr/bin/env python2
#
# Copyright 2018 Tim Hatch
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

import sys
import tabulate

def cmprow(a, b):
    ret = []
    for ai, bi in zip(a, b):
        if ai == a[-1]:
            # memory
            ret.append("%+.fkB %+.2f%%" % ((bi-ai), 100.0-(ai/bi*100.0)))
        else:
            ret.append("%+.2fms %+.2f%%" % ((bi-ai)*1000, 100.0-(ai/bi*100.0)))
    return tuple(ret)

def main(filename):
    # key is (pat, run), value is [all the results]
    known = {}

    cols = [
        "pat", "run", "init", "x[0]", ".", "x[1]", ".", "x[-2]", ".", "x[-1]", ".",
        "x[:10]", ".", "x[-10:]", ".", "peak_kb"]
    rows = []

    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split('\t')
            key = tuple(parts[:2])
            vals = list(map(float, parts[2:]))
            known[key] = vals
            if parts[1] != 'baseline':
                rows.append(key + cmprow(known[(parts[0], "baseline")], vals))
            #rows.append(parts)

    print(tabulate.tabulate(rows, cols))

if __name__ == '__main__':
    main(sys.argv[1])
