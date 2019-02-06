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

from mediatimestamp.immutable import Timestamp as ImmutableTimestamp
from mediatimestamp.immutable import TimeOffset as ImmutableTimeOffset
from mediatimestamp.immutable import TimeRange as ImmutableTimeRange

from mediatimestamp.mutable import Timestamp as MutableTimestamp
from mediatimestamp.mutable import TimeOffset as MutableTimeOffset
from mediatimestamp.mutable import TimeRange as MutableTimeRange


__all__ = ["timestamps", "timeoffsets", "timeranges", "disjoint_timeranges",
           "immutabletimestamps", "immutabletimeoffsets", "immutabletimeranges", "disjoint_immutabletimeranges",
           "mutabletimestamps", "mutabletimeoffsets", "mutabletimeranges", "disjoint_mutabletimeranges"]

MIN_IMMUTABLETIMESTAMP = ImmutableTimestamp(ImmutableTimestamp.MAX_SECONDS, ImmutableTimestamp.MAX_NANOSEC - 1, -1)
MAX_IMMUTABLETIMESTAMP = ImmutableTimestamp(ImmutableTimestamp.MAX_SECONDS, ImmutableTimestamp.MAX_NANOSEC - 1)

MIN_IMMUTABLETIMEOFFSET = ImmutableTimeOffset(ImmutableTimeOffset.MAX_SECONDS, ImmutableTimeOffset.MAX_NANOSEC - 1, -1)
MAX_IMMUTABLETIMEOFFSET = ImmutableTimestamp(ImmutableTimeOffset.MAX_SECONDS, ImmutableTimeOffset.MAX_NANOSEC - 1)


#
# Immutable versions. It is recommended to use these where possible
#

def immutabletimestamps(min_value=MIN_IMMUTABLETIMESTAMP, max_value=MAX_IMMUTABLETIMESTAMP):
    """Draw from this strategy to get immutable timestamps between the given minimum and maximum values.
    Shrinks towards earlier timestamps."""

    # This is pretty straightforward: generates integers in the right range and interprets then as nanosecond values to
    # generate Timestamps with
    return integers(min_value=min_value.to_nanosec(),
                    max_value=max_value.to_nanosec()).map(ImmutableTimestamp.from_nanosec)


def immutabletimeoffsets(min_value=MIN_IMMUTABLETIMEOFFSET, max_value=MAX_IMMUTABLETIMEOFFSET):
    """Draw from this strategy to get immutable timeoffsets between the given minimum and maximum values.
    Shrinks towards zero."""

    # This is pretty straightforward: generates integers in the right range and interprets then as nanosecond values to
    # generate TimeOffsets with
    return integers(min_value=min_value.to_nanosec(),
                    max_value=max_value.to_nanosec()).map(ImmutableTimeOffset.from_nanosec)


def immutabletimeranges_of_length(length,
                                  in_range=ImmutableTimeRange.eternity(),
                                  inclusivity=ImmutableTimeRange.INCLUSIVE):
    min_value = in_range.start if in_range.start is not None else MIN_IMMUTABLETIMESTAMP
    max_value = (in_range.end if in_range.end is not None else MAX_IMMUTABLETIMESTAMP) - length

    # This is also straightforward in a way: generate a timestamp in the range and then create a timerange of length
    # starting at that timestamp
    return (immutabletimestamps(min_value=min_value, max_value=max_value)
            .map(lambda start: ImmutableTimeRange.from_start_length(start, length, inclusivity)))


def immutabletimeranges(in_range=ImmutableTimeRange.eternity(),
                        inclusivity=ImmutableTimeRange.INCLUSIVE):
    """Draw from this strategy to get non-empty immutable timeranges with the specified inclusivity completely contained
    in the specified range. Shrinks towards smaller ranges and earlier ones."""
    max_length = in_range.length if not isinstance(in_range.length, float) else MAX_IMMUTABLETIMESTAMP

    # This is a tad more complex: each time a range is drawn from this we generate a timestamp to use as a length and
    # then generate a timerange of that length
    return (immutabletimestamps(min_value=MIN_IMMUTABLETIMESTAMP, max_value=max_length)
            .flatmap(lambda l: immutabletimeranges_of_length(l, in_range=in_range, inclusivity=inclusivity)))


def disjoint_immutabletimeranges(in_range=ImmutableTimeRange.eternity(), min_size=0, max_size=None):
    """Draw from this strategy to get lists of non-overlapping immutable TimeRange classes all of which will be
    inclusive and contained within the specified range.

    Shrinks towards fewer ranges, smaller ones, and earlier ones."""

    min_value = in_range.start if in_range.start is not None else MIN_IMMUTABLETIMESTAMP
    max_value = in_range.end if in_range.end is not None else MAX_IMMUTABLETIMESTAMP

    # The most complex, probably. Each time an item is drawn generate an integer and use it as a list size,
    # then generate a list of that length of timestamps. Then sort them into ascending order. Then use each adjacent
    # pair as the start and end of a timerange. Finally reject any lists of timeranges where some timeranges overlap
    # (the construction ensures that the only way this can happen is if the overlap is a single timestamp)
    return (integers(min_value=min_size, max_value=max_size)
            .flatmap(lambda n: lists(
                immutabletimestamps(min_value=min_value, max_value=max_value),
                min_size=2*n,
                max_size=2*n
            )).map(sorted).map(
                lambda l: [ImmutableTimeRange(l[2*x+0], l[2*x+1], ImmutableTimeRange.INCLUSIVE)
                           for x in range(0, len(l)//2)]
            ).filter(
                lambda l: all(l[x].end != l[x+1].start for x in range(0, len(l) - 1))
            ))


#
# Mutable versions for backwards compatibility. There's no good reason to need these.
#

MIN_MUTABLETIMESTAMP = MutableTimestamp(0, 0)
MAX_MUTABLETIMESTAMP = MutableTimestamp(MutableTimestamp.MAX_SECONDS, MutableTimestamp.MAX_NANOSEC - 1)

MIN_MUTABLETIMEOFFSET = MutableTimeOffset(MutableTimeOffset.MAX_SECONDS, MutableTimeOffset.MAX_NANOSEC - 1, -1)
MAX_MUTABLETIMEOFFSET = MutableTimestamp(MutableTimeOffset.MAX_SECONDS, MutableTimeOffset.MAX_NANOSEC - 1)


def mutabletimestamps(min_value=MIN_MUTABLETIMESTAMP, max_value=MAX_MUTABLETIMESTAMP):
    """Draw from this strategy to get mutable timestamps between the given minimum and maximum values.
    Shrinks towards earlier timestamps."""

    return (immutabletimestamps(min_value=ImmutableTimestamp.from_timeoffset(min_value),
                                max_value=ImmutableTimestamp.from_timeoffset(max_value))
            .map(MutableTimestamp.from_timeoffset))


def mutabletimeoffsets(min_value=MIN_MUTABLETIMEOFFSET, max_value=MAX_MUTABLETIMEOFFSET):
    """Draw from this strategy to get mutable timeoffsets between the given minimum and maximum values.
    Shrinks towards zero."""

    return (immutabletimeoffsets(min_value=ImmutableTimeOffset.from_timeoffset(min_value),
                                 max_value=ImmutableTimeOffset.from_timeoffset(max_value))
            .map(MutableTimeOffset.from_timeoffset))


def mutabletimeranges(in_range=MutableTimeRange.eternity(), inclusivity=MutableTimeRange.INCLUSIVE):
    """Draw from this strategy to get non-empty mutable timeranges with the specified inclusivity completely contained
    in the specified range. Shrinks towards smaller ranges and earlier ones."""

    return immutabletimeranges(in_range=ImmutableTimeRange.from_timerange(in_range),
                               inclusivity=inclusivity).map(MutableTimeRange.from_timerange)


def disjoint_mutabletimeranges(in_range=MutableTimeRange.eternity(), min_size=0, max_size=None):
    """Draw from this strategy to get lists of non-overlapping mutable TimeRange classes all of which will be
    inclusive and contained within the specified range.

    Shrinks towards fewer ranges, smaller ones, and earlier ones."""

    return disjoint_immutabletimeranges(in_range=ImmutableTimeRange.from_timerange(in_range),
                                        min_size=min_size,
                                        max_size=max_size).map(MutableTimeRange.from_timerange)


#
# In a future version these will become aliases for the immutable versions
#
timeoffsets = mutabletimeoffsets
timestamps = mutabletimestamps
timeranges = mutabletimeranges
disjoint_timeranges = disjoint_mutabletimeranges
