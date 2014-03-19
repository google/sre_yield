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

import re
import sre_constants
import sre_parse
import string
import sys
import types


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


class WrappedSequence(object):
    """This wraps a sequence, purely as a base clase for the other uses."""

    def __init__(self, raw):
        # Derived classes will likely override this constructor
        self.raw = raw
        # Note that we can't use the function len() because it insists on trying
        # to convert the returned number from a long-int to an ordinary int.
        self.length = raw.__len__()

    def get_item(self, i):
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
        if i < -self.length or i >= self.length:
            raise IndexError('Index %i vs length %i' % (i, self.length))
        # Usually we just call the user-provided function
        return self.get_item(i)

    def __iter__(self):
        for i in xrange(self.length):
            yield self.get_item(i)


class SlicedSequence(WrappedSequence):
    """This is part of an immutable and potentially arbitrarily long list."""

    def __init__(self, raw, slicer=None):
        # Derived classes will likely override this constructor
        self.raw = raw
        if slicer is None:
            self.start, self.stop, self.steps = 0, raw.__len__(), 1
        else:
            self.start, self.stop, self.steps = slicer.indices(raw.__len__())
        # integer round up
        self.length = ((self.stop - self.start + abs(self.steps) - 1) /
                       abs(self.steps))

    def get_item(self, i):
        j = i * self.steps + self.start
        return self.raw[j]


class ConcatenatedSequence(WrappedSequence):
    """This is equivalent to using extend() but without unpacking the lists."""

    def __init__(self, *alternatives):
        self.list_lengths = [(a, a.__len__()) for a in alternatives]
        self.length = sum(a_len for _, a_len in self.list_lengths)

    def get_item(self, i):
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

    def get_item(self, i):
        result = []
        for c, c_len in self.list_lengths:
            result.append(c[i % c_len])
            i //= c_len
        return ''.join(result)

    def __repr__(self):
        return '{combin ' + repr(self.list_lengths) + '}'


class RepetitiveSequence(WrappedSequence):
    """This chooses an entry from a list, many times, and concatenates."""

    def __init__(self, content, lowest=1, highest=1):
        self.content = content
        self.content_length = content.__len__()
        sublength = self.content_length ** lowest
        self.count_length = []
        for count in xrange(lowest, highest + 1):
            self.count_length.append((count, sublength))
            sublength *= self.content_length
        self.length = sum(c for _, c in self.count_length)

    def get_item(self, i):
        """Finds out how many repeats this index implies, then picks strings."""
        for count, sublength in self.count_length:
            if i >= sublength:
                i -= sublength
                continue
            result = []
            for _ in xrange(count):
                i, idx = divmod(i, self.content_length)
                result.append(self.content[idx])
            # smallest place value ends up on the right
            return ''.join(result[::-1])
        raise IndexError('Too Big')

    def __repr__(self):
        return '{repeat ' + repr(self.count_length) + '}'


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
        return ['<<<%s>>>' % repr(parsed)]

    def __init__(self, pattern, flags=0, charset=CHARSET, max_count=None):
        # If the RE module cannot compile it, we give up quickly
        self.matcher = re.compile(r'(?:%s)\Z' % pattern, flags)
        if not flags & re.DOTALL:
          charset = ''.join(c for c in charset if c != '\n')
        self.charset = charset

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

        # Configure the parser backends
        self.backends = {
            sre_constants.LITERAL: lambda y: [chr(y)],
            sre_constants.RANGE: lambda l, h: [chr(c) for c in xrange(l, h+1)],
            sre_constants.SUBPATTERN: lambda _, items: self.sub_values(items),
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
        }
        # Now build a generator that knows all possible patterns
        self.raw = self.sub_values(sre_parse.parse(pattern, flags))
        # Configure this class instance to know about that result
        self.length = self.raw.__len__()

    def __contains__(self, item):
        # Since we have a regex, we can search the list really cheaply
        return self.matcher.match(item) is not None


def Values(regex, flags=0, charset=CHARSET, max_count=None):
    """Function wrapper that hides the class constructor details."""
    return RegexMembershipSequence(regex, flags, charset, max_count=max_count)


def main(argv):
    """This module can be executed on the command line for testing."""
    for arg in argv[1:]:
        for i in Values(arg):
            print i


if __name__ == '__main__':
    main(sys.argv)
