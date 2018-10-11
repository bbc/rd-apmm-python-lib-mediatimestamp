#!/usr/bin/python
#
# Copyright 2018 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

"""Hypothesis ( https://hypothesis.readthedocs.io/en/latest/ ) is a library used for generating data driven testing in
python. When used it requires "strategies", which are special data generators used by its engine to produce large
quantities of data to test hypothetical features of software.

This module provides additional strategies for hypothesis which generate the types of objects provided by this library,
it will be of use if using hypothesis to test code which depends upon mediatimestamp.
"""

from __future__ import print_function
from __future__ import absolute_import

from hypothesis.strategies import integers, lists

from mediatimestamp import Timestamp, TimeOffset, TimeRange


__all__ = ["timestamps", "timeoffsets", "timeranges", "disjoint_timeranges"]

MIN_TIMESTAMP = Timestamp(0, 0)
MAX_TIMESTAMP = Timestamp(Timestamp.MAX_SECONDS, Timestamp.MAX_NANOSEC - 1)

MIN_TIMEOFFSET = TimeOffset(-TimeOffset.MAX_SECONDS, TimeOffset.MAX_NANOSEC - 1)
MAX_TIMEOFFSET = Timestamp(TimeOffset.MAX_SECONDS, TimeOffset.MAX_NANOSEC - 1)


def timestamps(min_value=MIN_TIMESTAMP, max_value=MAX_TIMESTAMP):
    """Draw from this strategy to get timestamps between the given minimum and maximum values.
    Shrinks towards earlier timestamps."""

    # This is pretty straightforward: generates integers in the right range and interprets then as nanosecond values to
    # generate Timestamps with
    return integers(min_value=min_value.to_nanosec(), max_value=max_value.to_nanosec()).map(Timestamp.from_nanosec)


def timeoffsets(min_value=MIN_TIMEOFFSET, max_value=MAX_TIMEOFFSET):
    """Draw from this strategy to get timeoffsets between the given minimum and maximum values.
    Shrinks towards zero."""

    # This is pretty straightforward: generates integers in the right range and interprets then as nanosecond values to
    # generate TimeOffsets with
    return integers(min_value=min_value.to_nanosec(), max_value=max_value.to_nanosec()).map(TimeOffset.from_nanosec)


def timeranges_of_length(length, in_range=TimeRange.eternity(), inclusivity=TimeRange.INCLUSIVE):
    min_value = in_range.start if in_range.start is not None else MIN_TIMESTAMP
    max_value = (in_range.end if in_range.end is not None else MAX_TIMESTAMP) - length

    # This is also straightforward in a way: generate a timestamp in the range and then create a timerange of length
    # starting at that timestamp
    return (timestamps(min_value=min_value, max_value=max_value)
            .map(lambda start: TimeRange.from_start_length(start, length, inclusivity)))


def timeranges(in_range=TimeRange.eternity(), inclusivity=TimeRange.INCLUSIVE):
    """Draw from this strategy to get non-empty timeranges with the specified inclusivity completely contained in the
    specified range. Shrinks towards smaller ranges and earlier ones."""
    max_length = in_range.length if not isinstance(in_range.length, float) else MAX_TIMESTAMP

    # This is a tad more complex: each time a range is drawn from this we generate a timestamp to use as a length and
    # then generate a timerange of that length
    return (timestamps(min_value=MIN_TIMESTAMP, max_value=max_length)
            .flatmap(lambda l: timeranges_of_length(l, in_range=in_range, inclusivity=inclusivity)))


def disjoint_timeranges(in_range=TimeRange.eternity(), min_size=0, max_size=None):
    """Draw from this strategy to get lists of non-overlapping TimeRange classes all of which will be inclusive and
    contained within the specified range.

    Shrinks towards fewer ranges, smaller ones, and earlier ones."""

    min_value = in_range.start if in_range.start is not None else MIN_TIMESTAMP
    max_value = in_range.end if in_range.end is not None else MAX_TIMESTAMP

    # The most complex, probably. Each time an item is drawn generate an integer and use it as a list size,
    # then generate a list of that length of timestamps. Then sort them into ascending order. Then use each adjacent
    # pair as the start and end of a timerange. Finally reject any lists of timeranges where some timeranges overlap
    # (the construction ensures that the only way this can happen is if the overlap is a single timestamp)
    return (integers(min_value=min_size, max_value=max_size)
            .flatmap(lambda n: lists(
                timestamps(min_value=min_value, max_value=max_value),
                min_size=2*n,
                max_size=2*n
            )).map(sorted).map(
                lambda l: [TimeRange(l[2*x+0], l[2*x+1], TimeRange.INCLUSIVE) for x in range(0, len(l)//2)]
            ).filter(
                lambda l: all(l[x].end != l[x+1].start for x in range(0, len(l) - 1))
            ))
