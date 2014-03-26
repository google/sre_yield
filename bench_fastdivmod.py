#!/usr/bin/env python2

import signal
import sys
import math
import time
import multiprocessing
import traceback

import fastdivmod

MIN_TIME = 4.0
MIN_TRIALS = 3

MULTIPLIER = 1 # for very fast things, tweak > 1

RED = 31
GREEN = 32

def hilite(num, text):
    return '\033[%dm%s\033[0m' % (num, text)

def consume(it):
    """Simply exhaust the iterator."""
    for _ in it:
        pass

def time_trial(func, args, kwargs):
    trials = 0
    t0 = time.time()
    t1 = t0
    while t1 < t0 + MIN_TIME or trials < MIN_TRIALS:
        consume(func(*args, **kwargs))
        trials += 1
        t1 = time.time()
    avg = (t1 - t0) / trials * MULTIPLIER
    return avg

def pool_runner((trial_type, bignum, a, divisor)):
    if trial_type == 'basic':
        func = fastdivmod.basic_divmod
        args = [bignum, divisor]
    elif trial_type == 'def':
        func = fastdivmod.genmod
        args = [bignum, divisor]
    elif trial_type == 'auto':
        func = fastdivmod.divmod_iter
        args = [bignum, divisor]
    elif trial_type == 'mult':
        chunk = fastdivmod.find_largest_power(sys.maxint * a, divisor)
        func = fastdivmod.genmod
        args = [bignum, divisor, chunk]
        if a < 1:
            trial_type = '%.2fmi' % (a,)
        else:
            trial_type = '%dmi' % (a,)

        if chunk <= divisor:
            return 'n/a', trial_type

    elif trial_type == 'pow':
        chunk = fastdivmod.find_largest_power(sys.maxint ** a, divisor)
        func = fastdivmod.genmod
        args = [bignum, divisor, chunk]
        if a < 0:
            trial_type = 'mi^%.2f' % (a,)
        else:
            trial_type = 'mi^%d' % (a,)

        if chunk <= divisor:
            return 'n/a', trial_type

    elif trial_type == 'dpow':
        chunk = divisor ** a
        func = fastdivmod.genmod
        args = [bignum, divisor, chunk]
        if a < 0:
            trial_type = 'd^%.2f' % (a,)
        else:
            trial_type = 'd^%d' % (a,)
    try:
        return time_trial(func, args, {}), trial_type
    except Exception, e:
        print "\nException on", func, a, chunk, divisor, trial_type
        traceback.print_exc()
        raise


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def main(argv):
    bignum = 255**20000
    workers = multiprocessing.cpu_count() - 2

    for arg in argv:
        if arg.startswith('n='):
            bignum = eval(arg[2:])
        elif arg.startswith('m='):
            globals()['MULTIPLIER'] = eval(arg[2:])
        elif arg.startswith('ncpu='):
            workers = int(arg[5:])
        else:
            raise NotImplementedError("Unknown arg %r" % (arg,))

    print "%d decimal digits, multiplier %d" % (
        math.log(bignum) / math.log(10), MULTIPLIER)

    divisors = (2, 10, 254, 255, 1024, sys.maxint, sys.maxint**2, sys.maxint**4)
    best = [sys.maxint] * len(divisors)

    print "chunk\t",
    def trunc(x):
        if len(str(x)) > 6:
            return "%.1e" % (x,)
        else:
            return str(x)

    mult_factors = (0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 1024, 2058, 4096)
    pow_factors = (2, 4, 8)
    dpow_factors = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)

    tests_l1 = [('basic', bignum, None),
                ('def', bignum, None),
                ('auto', bignum, None)] + \
               [('mult', bignum, a) for a in mult_factors] + \
               [('pow', bignum, a) for a in pow_factors] + \
               [('dpow', bignum, a) for a in dpow_factors]

    tests_l2 = [t + (d,) for t in tests_l1 for d in divisors]

    print "\t".join(map(trunc, divisors))
    prev_label = None

    # Chrome always eats up about 1 cpu; either boost priority or subtract here.
    pool = multiprocessing.Pool(multiprocessing.cpu_count() - 2, init_worker)
    try:
        for result, trial_type in pool.imap(pool_runner, tests_l2, chunksize=2):
            if trial_type != prev_label:
                if prev_label is not None:
                    sys.stdout.write('\n')
                sys.stdout.write('%s\t' % (trial_type,))
                prev_label = trial_type
                col = 0

            if not isinstance(result, str):
                if result < best[col] and sys.stdout.isatty():
                    best[col] = result
                    result = hilite(GREEN, '%.05f' % (result,))
                else:
                    result = '%.05f' % (result,)

            sys.stdout.write(result+'\t')
            sys.stdout.flush()
            col += 1
    except KeyboardInterrupt:
        sys.stdout.write("KeyboardInterrupt, please wait...")
        sys.stdout.flush()

        pool.terminate()

    print

if __name__ == '__main__':
    main(sys.argv[1:])
