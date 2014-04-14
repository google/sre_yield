#!/usr/bin/env python2
#
# Copyright 2011-2014 Google Inc.
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

"""This module can generate all strings that match a regular expression.

The regex is parsed using the SRE module that is standard in python,
then the data structure is executed to form a bunch of iterators.
"""

__author__ = 'alexperry@google.com (Alex Perry)'
__all__ = ['Values', 'AllStrings', 'AllMatches', 'ParseError']


import bisect
import math
import re
import sre_constants
import sre_parse
import string
import sys
import types

from sre_yield import cachingseq
from sre_yield import fastdivmod

_RE_METACHARS = r'$^{}*+\\'
_ESCAPED_METACHAR = r'\\[' + _RE_METACHARS + r']'
ESCAPED_METACHAR_RE = re.compile(_ESCAPED_METACHAR)
CHARSET = [chr(c) for c in xrange(256)]

WORD = string.letters + string.digits + '_'

def Not(chars):
    return ''.join(sorted(set(CHARSET) - set(chars)))


CATEGORIES = {
    sre_constants.CATEGORY_WORD: WORD,
    sre_constants.CATEGORY_NOT_WORD: Not(WORD),
    sre_constants.CATEGORY_DIGIT: string.digits,
    sre_constants.CATEGORY_NOT_DIGIT: Not(string.digits),
    sre_constants.CATEGORY_SPACE: string.whitespace,
    sre_constants.CATEGORY_NOT_SPACE: Not(string.whitespace),
}

# This constant varies between builds of Python; this is the lower value.
MAX_REPEAT_COUNT = 65535


class ParseError(Exception):
    pass


def slice_indices(slice_obj, size):
    """slice_obj.indices() except this one supports longs."""
    # start stop step
    start = slice_obj.start
    stop = slice_obj.stop
    step = slice_obj.step

    # We don't always update a value for negative indices (if we wrote it here
    # due to None).
    if step is None:
        step = 1
    if start is None:
        if step > 0:
            start = 0
        else:
            start = size - 1
    else:
        start = _adjust_index(start, size)

    if stop is None:
        if step > 0:
            stop = size
        else:
            stop = -1
    else:
        stop = _adjust_index(stop, size)

    return (start, stop, step)


def _adjust_index(n, size):
    if n < 0:
        n += size

    if n < 0:
        raise IndexError("Out of range")
    if n > size:
        n = size
    return n


def _xrange(*args):
    """Because xrange doesn't support longs :("""
    # prefer real xrange if it works
    try:
        return xrange(*args)
    except OverflowError:
        return _bigrange(*args)


def _bigrange(*args):
    if len(args) == 1:
        start = 0; stop = args[0]; step = 1
    elif len(args) == 2:
        start, stop = args
        step = 1
    elif len(args) == 3:
        start, stop, step = args
    else:
        raise ValueError("Too many args for _bigrange")

    i = start
    while True:
        yield i
        i += step
        if step < 0 and i <= stop:
            break
        if step > 0 and i >= stop:
            break


class WrappedSequence(object):
    """This wraps a sequence, purely as a base clase for the other uses."""

    def __init__(self, raw):
        # Derived classes will likely override this constructor
        self.raw = raw
        # Note that we can't use the function len() because it insists on trying
        # to convert the returned number from a long-int to an ordinary int.
        self.length = raw.__len__()

    def get_item(self, i, d=None):
        i = _adjust_index(i, self.length)
        if hasattr(self.raw, 'get_item'):
            return self.raw.get_item(i, d)
        return self.raw[i]

    def __len__(self):
        return self.length

    def __getitem__(self, i):
        # If the user wanted a slice, we provide a wrapper
        if isinstance(i, types.SliceType):
            result = SlicedSequence(self, slicer=i)
            if result.__len__() < 16:
                # Short lists are unpacked
                result = [item for item in result]
            return result
        i = _adjust_index(i, self.length)
        # Usually we just call the user-provided function
        return self.get_item(i)

    def __iter__(self):
        for i in _xrange(self.length):
            yield self.get_item(i)


def _sign(x):
    if x > 0:
        return 1
    else:
        return -1


class SlicedSequence(WrappedSequence):
    """This is part of an immutable and potentially arbitrarily long list."""

    def __init__(self, raw, slicer=None):
        # Derived classes will likely override this constructor
        self.raw = raw
        if slicer is None:
            self.start, self.stop, self.step = 0, raw.__len__(), 1
        else:
            self.start, self.stop, self.step = slice_indices(slicer, raw.__len__())

        # Integer round up, depending on step direction
        self.length = ((self.stop - self.start + self.step - _sign(self.step)) /
                       self.step)

    def get_item(self, i, d=None):
        j = i * self.step + self.start
        return self.raw[j]


class ConcatenatedSequence(WrappedSequence):
    """This is equivalent to using extend() but without unpacking the lists."""

    def __init__(self, *alternatives):
        self.list_lengths = [(a, a.__len__()) for a in alternatives]
        self.length = sum(a_len for _, a_len in self.list_lengths)

    def get_item(self, i, d=None):
        for a, a_len in self.list_lengths:
            if i < a_len:
                return a[i]
            i -= a_len
        raise IndexError('Too Big')

    def __contains__(self, item):
        for a, _ in self.list_lengths:
            if item in a:
                return True
        return False

    def __repr__(self):
        return '{concat ' + repr(self.list_lengths) + '}'


class CombinatoricsSequence(WrappedSequence):
    """This uses all combinations of one item from each passed list."""

    def __init__(self, *components):
        self.list_lengths = [(a, a.__len__()) for a in components]
        self.length = 1
        for _, c_len in self.list_lengths:
            self.length *= c_len

    def get_item(self, i, d=None):
        result = []
        if i < 0:
            i += self.length
        if i < 0 or i >= self.length:
            raise IndexError("Index %d out of bounds" % (i,))

        if len(self.list_lengths) == 1:
            # skip unnecessary ''.join -- big speedup
            return self.list_lengths[0][0][i]

        for c, c_len in self.list_lengths:
            i, mod = divmod(i, c_len)
            if hasattr(c, 'get_item'):
                result.append(c.get_item(mod, d))
            else:
                result.append(c[mod])
        return ''.join(result)

    def __repr__(self):
        return '{combin ' + repr(self.list_lengths) + '}'


class RepetitiveSequence(WrappedSequence):
    """This chooses an entry from a list, many times, and concatenates."""

    def __init__(self, content, lowest=1, highest=1):
        self.content = content
        self.content_length = content.__len__()
        self.length = fastdivmod.powersum(self.content_length, lowest, highest)
        self.lowest = lowest
        self.highest = highest

        def arbitrary_entry(i):
            return (fastdivmod.powersum(self.content_length, lowest, i+lowest-1), i+lowest)

        def entry_from_prev(i, prev):
            return (prev[0] + (self.content_length ** prev[1]), prev[1] + 1)

        self.offsets = cachingseq.CachingFuncSequence(
            arbitrary_entry, highest - lowest+1, entry_from_prev)
        # This needs to be a constant in order to reuse caclulations in future
        # calls to bisect (a moving target will produce more misses).
        if self.offsets[-1][0] > sys.maxint:
            i = 0
            while i + 2 < len(self.offsets):
                if self.offsets[i+1][0] > sys.maxint:
                    self.index_of_offset = i
                    self.offset_break = self.offsets[i][0]
                    break
                i += 1
        else:
            self.index_of_offset = len(self.offsets)
            self.offset_break = sys.maxint

    def get_item(self, i, d=None):
        """Finds out how many repeats this index implies, then picks strings."""
        if i < self.offset_break:
            by_bisect = bisect.bisect_left(self.offsets, (i, -1), hi=self.index_of_offset)
        else:
            by_bisect = bisect.bisect_left(self.offsets, (i, -1), lo=self.index_of_offset)

        if by_bisect == len(self.offsets) or self.offsets[by_bisect][0] > i:
            by_bisect -= 1

        num = i - self.offsets[by_bisect][0]
        count = self.offsets[by_bisect][1]

        if count > 100 and self.content_length < 1000:
            content = list(self.content)
        else:
            content = self.content

        result = []

        if count == 0:
            return ''

        for modulus in fastdivmod.divmod_iter(num, self.content_length):
            result.append(content[modulus])

        leftover = count - len(result)
        if leftover:
            assert leftover > 0
            result.extend([content[0]] * leftover)

        # smallest place value ends up on the right
        return ''.join(result[::-1])

    def __repr__(self):
        return '{repeat base=%d low=%d high=%d}' % (self.content_length, self.lowest, self.highest)


class SaveCaptureGroup(WrappedSequence):
    def __init__(self, parsed, key):
        self.key = key
        super(SaveCaptureGroup, self).__init__(parsed)

    def get_item(self, n, d=None):
        rv = super(SaveCaptureGroup, self).get_item(n, d)
        if d is not None:
            d[self.key] = rv
        return rv


class ReadCaptureGroup(WrappedSequence):
    def __init__(self, n):
        self.num = n
        self.length = 1

    def get_item(self, i, d=None):
        if i != 0:
            raise IndexError(i)
        if d is None:
            raise ValueError('ReadCaptureGroup with no dict')
        return d.get(self.num, "fail")


class RegexMembershipSequence(WrappedSequence):
    """Creates a sequence from the regex, knows how to test membership."""

    def empty_list(self, *_):
        return []

    def branch_values(self, _, items):
        """Converts SRE parser data into literals and merges those lists."""
        return ConcatenatedSequence(
            *[self.sub_values(parsed) for parsed in items])

    def max_repeat_values(self, min_count, max_count, items):
        """Sequential expansion of the count to be combinatorics."""
        max_count = min(max_count, self.max_count)
        return RepetitiveSequence(
            self.sub_values(items), min_count, max_count)

    def in_values(self, items):
        # Special case which distinguishes branch from charset operator
        if items and items[0][0] == sre_constants.NEGATE:
            items = self.branch_values(None, items[1:])
            return [item for item in self.charset if item not in items]
        return self.branch_values(None, items)

    def not_literal(self, y):
        return self.in_values(((sre_constants.NEGATE,),
                              (sre_constants.LITERAL, y),))

    def category(self, y):
        return CATEGORIES[y]

    def groupref(self, n):
        self.has_groupref = True
        return ReadCaptureGroup(n)

    def get_item(self, i, d=None):
        """Typically only pass i.  d is an internal detail, for consistency with other classes.

        If you care about the capture groups, you should use
        RegexMembershipSequenceMatches instead, which returns a Match object
        instead of a string."""
        if self.has_groupref or d is not None:
            if d is None:
                d = {}
            return super(RegexMembershipSequence, self).get_item(i, d)
        else:
            return super(RegexMembershipSequence, self).get_item(i)

    def sub_values(self, parsed):
        """This knows how to convert one piece of parsed pattern."""
        # If this is a subpattern object, we just want its data
        if isinstance(parsed, sre_parse.SubPattern):
            parsed = parsed.data
        # A list indicates sequential elements of a string
        if isinstance(parsed, list):
            elements = [self.sub_values(p) for p in parsed]
            return CombinatoricsSequence(*elements)
        # If not a list, a tuple represents a specific match type
        if isinstance(parsed, tuple) and parsed:
            matcher, arguments = parsed
            if not isinstance(arguments, tuple):
                arguments = (arguments,)
            if matcher in self.backends:
                return self.backends[matcher](*arguments)
        # No idea what to do here
        raise ParseError(repr(parsed))

    def maybe_save(self, group, parsed):
        rv = self.sub_values(parsed)
        if group is not None:
            rv = SaveCaptureGroup(rv, group)
        return rv

    def __init__(self, pattern, flags=0, charset=CHARSET, max_count=None):
        # If the RE module cannot compile it, we give up quickly
        self.matcher = re.compile(r'(?:%s)\Z' % pattern, flags)
        if not flags & re.DOTALL:
            charset = ''.join(c for c in charset if c != '\n')
        self.charset = charset

        self.named_group_lookup = self.matcher.groupindex

        if flags & re.IGNORECASE:
            raise ParseError('Flag "i" not supported. https://code.google.com/p/sre-yield/issues/detail?id=7')
        elif flags & re.UNICODE:
            raise ParseError('Flag "u" not supported. https://code.google.com/p/sre-yield/issues/detail?id=8')
        elif flags & re.LOCALE:
            raise ParseError('Flag "l" not supported. https://code.google.com/p/sre-yield/issues/detail?id=8')

        if max_count is None:
            self.max_count = MAX_REPEAT_COUNT
        else:
            self.max_count = max_count

        self.has_groupref = False

        # Configure the parser backends
        self.backends = {
            sre_constants.LITERAL: lambda y: [chr(y)],
            sre_constants.RANGE: lambda l, h: [chr(c) for c in xrange(l, h+1)],
            sre_constants.SUBPATTERN: self.maybe_save,
            sre_constants.BRANCH: self.branch_values,
            sre_constants.MIN_REPEAT: self.max_repeat_values,
            sre_constants.MAX_REPEAT: self.max_repeat_values,
            sre_constants.AT: self.empty_list,
            sre_constants.ASSERT: self.empty_list,
            sre_constants.ASSERT_NOT: self.empty_list,
            sre_constants.ANY:
                lambda _: self.in_values(((sre_constants.NEGATE,),)),
            sre_constants.IN: self.in_values,
            sre_constants.NOT_LITERAL: self.not_literal,
            sre_constants.CATEGORY: self.category,
            sre_constants.GROUPREF: self.groupref,
        }
        # Now build a generator that knows all possible patterns
        self.raw = self.sub_values(sre_parse.parse(pattern, flags))
        # Configure this class instance to know about that result
        self.length = self.raw.__len__()

    def __contains__(self, item):
        # Since we have a regex, we can search the list really cheaply
        return self.matcher.match(item) is not None


class RegexMembershipSequenceMatches(RegexMembershipSequence):
    def __getitem__(self, i):
        if isinstance(i, types.SliceType):
            result = SlicedSequence(self, slicer=i)
            if result.__len__() < 16:
                # Short lists are unpacked
                result = [item for item in result]
            return result

        d = {}
        s = super(RegexMembershipSequenceMatches, self).get_item(i, d)
        return Match(s, d, self.named_group_lookup)


def AllStrings(regex, flags=0, charset=CHARSET, max_count=None):
    """Constructs an object that will generate all matching strings."""
    return RegexMembershipSequence(regex, flags, charset, max_count=max_count)

Values = AllStrings


class Match(object):
    def __init__(self, string, groups, named_groups):
        # TODO keep group(0) only, and spans for the rest.
        self._string = string
        self._groups = groups
        self._named_groups = named_groups
        self.lastindex = len(groups) + 1

    def group(self, n=0):
        if n == 0:
            return self._string
        if not isinstance(n, int):
            n = self._named_groups[n]
        return self._groups[n]

    def groups(self):
        return tuple(self._groups[i] for i in range(1, self.lastindex))

    def groupdict(self):
        d = {}
        for k, v in self._named_groups.iteritems():
            d[k] = self._groups[v]
        return d

    def span(self, n=0):
        raise NotImplementedError()


def AllMatches(regex, flags=0, charset=CHARSET, max_count=None):
    """Constructs an object that will generate all matching strings."""
    return RegexMembershipSequenceMatches(regex, flags, charset, max_count=max_count)


def main(argv=None):
    """This module can be executed on the command line for testing."""
    if argv is None:
        argv = sys.argv
    for arg in argv[1:]:
        for i in AllStrings(arg):
            print i


if __name__ == '__main__':
    main()
