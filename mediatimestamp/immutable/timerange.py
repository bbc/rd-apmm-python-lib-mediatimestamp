# Copyright 2020 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from fractions import Fraction
from abc import ABCMeta, abstractmethod
from typing import Tuple, Union, Optional, cast, Iterator, Type, TYPE_CHECKING
from typing_extensions import Protocol, runtime_checkable

from ..constants import MAX_NANOSEC
from ..exceptions import TsValueError

from ._types import RationalTypes
from .timeoffset import TimeOffset, SupportsMediaTimeOffset, mediatimeoffset
from .timestamp import Timestamp, SupportsMediaTimestamp, mediatimestamp

__all__ = ["TimeRange", "SupportsMediaTimeRange", "mediatimerange"]


if TYPE_CHECKING:
    @runtime_checkable
    class SupportsMediaTimeRange (Protocol):
        def __mediatimerange__(self) -> "TimeRange":
            ...
else:
    class SupportsMediaTimeRange (metaclass=ABCMeta):
        """This is an abstract base class for any class that can be automagically converted into a TimeRange.

        To implement this simply implement the __mediatimerange__ magic method. No need to inherit from this
        class explicitly.
        """
        @classmethod
        def __subclasshook__(cls, subclass: Type) -> bool:
            if (
                issubclass(subclass, TimeRange) or
                hasattr(subclass, "__mediatimerange__") or
                issubclass(subclass, SupportsMediaTimestamp)
            ):
                return True
            else:
                return False

        @abstractmethod
        def __mediatimerange__(self) -> "TimeRange":
            ...


def mediatimerange(v: SupportsMediaTimeRange) -> "TimeRange":
    """This method can be called on any object which supports the __mediatimerange__ magic method
    and also on a TimeRange. It will always return a TimeRange or raise a ValueError.
    """
    if isinstance(v, TimeRange):
        return v
    elif hasattr(v, "__mediatimerange__"):
        return v.__mediatimerange__()
    elif isinstance(v, SupportsMediaTimestamp):
        return mediatimerange(mediatimestamp(v))
    else:
        raise ValueError("{!r} cannot be converted to a mediatimestamp.TimeRange".format(v))


class TimeRange (object):
    """A nanosecond immutable precision time range object"""

    class Inclusivity (int):
        def __and__(self, other: int) -> "TimeRange.Inclusivity":
            return TimeRange.Inclusivity(int(self) & int(other) & 0x3)

        def __or__(self, other: int) -> "TimeRange.Inclusivity":
            return TimeRange.Inclusivity((int(self) | int(other)) & 0x3)

        def __xor__(self, other: int) -> "TimeRange.Inclusivity":
            return TimeRange.Inclusivity((int(self) ^ int(other)) & 0x3)

        def __invert__(self) -> "TimeRange.Inclusivity":
            return TimeRange.Inclusivity((~int(self)) & 0x3)

    EXCLUSIVE = Inclusivity(0x0)
    INCLUDE_START = Inclusivity(0x1)
    INCLUDE_END = Inclusivity(0x2)
    INCLUSIVE = Inclusivity(0x3)

    class Rounding(int):
        pass

    ROUND_DOWN = Rounding(0)
    ROUND_NEAREST = Rounding(1)
    ROUND_UP = Rounding(2)
    ROUND_IN = Rounding(3)
    ROUND_OUT = Rounding(4)
    ROUND_START = Rounding(5)
    ROUND_END = Rounding(6)

    def __init__(self,
                 start: Optional[SupportsMediaTimestamp],
                 end: Optional[SupportsMediaTimestamp],
                 inclusivity: "TimeRange.Inclusivity" = INCLUSIVE):
        """Construct a time range starting at start and ending at end

        :param start: A Timestamp or None
        :param end: A Timestamp or None
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        super().__init__()
        self.start: Optional[Timestamp]
        self.end: Optional[Timestamp]
        self.inclusivity: TimeRange.Inclusivity

        # Convert convertible inputs
        if start is not None:
            start = mediatimestamp(start)
        if end is not None:
            end = mediatimestamp(end)

        # Normalise the 'never' cases
        if start is not None and end is not None:
            if start > end or (start == end and inclusivity != TimeRange.INCLUSIVE):
                start = Timestamp()
                end = Timestamp()
                inclusivity = TimeRange.EXCLUSIVE

        # Normalise the 'eternity' cases
        if start is None and end is None:
            inclusivity = TimeRange.INCLUSIVE

        self.__dict__['start'] = start
        self.__dict__['end'] = end
        self.__dict__['inclusivity'] = inclusivity

    def __setattr__(self, name: str, value: object) -> None:
        raise TsValueError("Cannot assign to an immutable TimeRange")

    def __mediatimerange__(self) -> "TimeRange":
        return self

    def __iter__(self) -> Iterator[Timestamp]:
        return self.at_rate(MAX_NANOSEC)

    def __reversed__(self) -> Iterator[Timestamp]:
        return self.reversed_at_rate(MAX_NANOSEC)

    def at_rate(self,
                numerator: RationalTypes,
                denominator: RationalTypes = 1,
                phase_offset: SupportsMediaTimeOffset = TimeOffset()) -> Iterator[Timestamp]:
        """Returns an iterable which yields Timestamp objects at the specified rate within the
        range starting at the beginning and moving later.

        :param numerator: The numerator for the rate in Hz (or the exact rate as a Fraction or float)
        :param denominator: The denominator for the rate in Hz
        :param phase_offset: A TimeOffset object which sets the phase offset of the first timestamp
                             drawn from the iterable.

        :raises: ValueError If a phase_offset is specified which is larger than the reciprocal of the rate

        :returns: an iterable that yields Timestamp objects
        """
        rate = Fraction(numerator, denominator)
        phase_offset = mediatimeoffset(phase_offset)
        if phase_offset >= TimeOffset.from_count(1, rate):
            raise ValueError("phase_offset of {} is too large for rate {}".format(phase_offset, rate))

        if self.start is None:
            raise ValueError("Cannot iterate over a timerange with no start")

        count = (self.start - phase_offset).to_count(rate)

        while True:
            ts = Timestamp.from_count(count, rate) + phase_offset
            count += 1

            if ts < self.start or ((self.inclusivity & TimeRange.INCLUDE_START) == 0 and ts == self.start):
                continue
            elif (self.end is not None and
                  (ts > self.end or ((self.inclusivity & TimeRange.INCLUDE_END) == 0 and ts == self.end))):
                break
            else:
                yield ts

    def reversed_at_rate(self,
                         numerator: RationalTypes,
                         denominator: RationalTypes = 1,
                         phase_offset: SupportsMediaTimeOffset = TimeOffset()) -> Iterator[Timestamp]:
        """Returns an iterable which yields Timestamp objects at the specified rate within the
        range starting at the end and moving earlier.

        :param numerator: The numerator for the rate in Hz (or the exact rate as a Fraction or float)
        :param denominator: The denominator for the rate in Hz
        :param phase_offset: A TimeOffset object which sets the phase offset of the first timestamp
                             drawn from the iterable.

        :raises: ValueError If a phase_offset is specified which is larger than the reciprocal of the rate

        :returns: an iterable that yields Timestamp objects
        """
        phase_offset = mediatimeoffset(phase_offset)
        rate = Fraction(numerator, denominator)
        if phase_offset >= TimeOffset.from_count(1, rate):
            raise ValueError("phase_offset of {} is too large for rate {}".format(phase_offset, rate))

        if self.end is None:
            raise ValueError("Cannot reverse iterate over a timerange with no end")

        count = (self.end - phase_offset).to_count(rate)

        while True:
            ts = Timestamp.from_count(count, rate) + phase_offset
            count -= 1

            if ts > self.end or ((self.inclusivity & TimeRange.INCLUDE_END) == 0 and ts == self.end):
                continue
            elif (self.start is not None and
                  (ts < self.start or ((self.inclusivity & TimeRange.INCLUDE_START) == 0 and ts == self.start))):
                break
            else:
                yield ts

    @classmethod
    def from_timerange(cls, other: SupportsMediaTimeRange) -> "TimeRange":
        """Construct an immutable timerange from another timerange"""
        other = mediatimerange(other)

        start: Optional[Timestamp] = None
        if other.start is not None:
            start = Timestamp.from_timeoffset(other.start)

        end: Optional[Timestamp] = None
        if other.end is not None:
            end = Timestamp.from_timeoffset(other.end)

        return TimeRange(start,
                         end,
                         other.inclusivity)

    @classmethod
    def from_start(cls, start: SupportsMediaTimestamp, inclusivity: "TimeRange.Inclusivity" = INCLUSIVE) -> "TimeRange":
        """Construct a time range starting at start with no end

        :param start: A Timestamp
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        return cls(start, None, inclusivity)

    @classmethod
    def from_end(cls, end: SupportsMediaTimestamp, inclusivity: "TimeRange.Inclusivity" = INCLUSIVE) -> "TimeRange":
        """Construct a time range ending at end with no start

        :param end: A Timestamp
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        return cls(None, end, inclusivity)

    @classmethod
    def from_start_length(cls,
                          start: SupportsMediaTimestamp,
                          length: SupportsMediaTimeOffset,
                          inclusivity: "TimeRange.Inclusivity" = INCLUSIVE) -> "TimeRange":
        """Construct a time range starting at start and ending at (start + length)

        :param start: A Timestamp
        :param length: A TimeOffset, which must be non-negative
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END

        :raises: TsValueError if the length is negative"""
        length = mediatimeoffset(length)
        start = mediatimestamp(start)
        if length < TimeOffset():
            raise TsValueError("Length must be non-negative")
        return cls(start, start + length, inclusivity)

    @classmethod
    def eternity(cls) -> "TimeRange":
        """Return an unbounded time range covering all time"""
        return cls(None, None)

    @classmethod
    def never(cls) -> "TimeRange":
        """Return a time range covering no time"""
        return cls(Timestamp(), Timestamp(), TimeRange.EXCLUSIVE)

    @classmethod
    def from_single_timestamp(cls, ts: SupportsMediaTimestamp) -> "TimeRange":
        """Construct a time range containing only a single timestamp

        :param ts: A Timestamp"""
        ts = mediatimestamp(ts)
        return cls(ts, ts, TimeRange.INCLUSIVE)

    @classmethod
    def from_str(cls, s: str, inclusivity: "TimeRange.Inclusivity" = INCLUSIVE) -> "TimeRange":
        """Convert a string to a time range.

        Valid ranges are:
        [<ts>_<ts>]
        [<ts>_<ts>)
        (<ts>_<ts>]
        (<ts>_<ts>)
        [<ts>]
        <ts>_<ts>
        <ts>
        ()

        where <ts> is any valid string format for Timestamp.from_str() or an empty string.

        The meaning of these is relatively simple: [ indicates including the start time,
        ( indicates excluding it, ] indicates including the end time, and ) indicates excludint it.
        If brackets are ommitted entirely then this is taken as an inclusive range at both ends.
        Omitting a timestamp indicates that there is no bound on that end (ie. the range goes on forever),
        including only a single timestamp by itself indicates a range containing exactly that one timestamp.
        Finally the string "()" represents the empty range.

        :param s: The string to process
        """
        m = re.match(r'(\[|\()?([^_\)\]]+)?(_([^_\)\]]+)?)?(\]|\))?', s)

        if m is None:
            raise ValueError("{!r} is not a valid TimeRange".format(s))

        inc = TimeRange.INCLUSIVE
        if m.group(1) == "(":
            inc &= ~TimeRange.INCLUDE_START
        if m.group(5) == ")":
            inc &= ~TimeRange.INCLUDE_END

        start_str = m.group(2)
        end_str = m.group(4)

        start: Optional[Timestamp] = None
        end: Optional[Timestamp] = None
        if start_str is not None:
            start = Timestamp.from_str(start_str)
        if end_str is not None:
            end = Timestamp.from_str(end_str)

        if start is None and end is None:
            # Ie. we have no first or second timestamp
            if m.group(3) is not None:
                # ie. we have a '_' character
                return cls.eternity()
            else:
                # We have no '_' character, so the whole range is empty
                return cls.never()
        elif start is not None and end is None and m.group(3) is None:
            # timestamp of form <ts>
            return cls.from_single_timestamp(start)
        else:
            return cls(start, end, inc)

    @property
    def length(self) -> Union[TimeOffset, float]:
        if self.end is None or self.start is None:
            return float("inf")
        return self.end - self.start

    def bounded_before(self) -> bool:
        return self.start is not None

    def bounded_after(self) -> bool:
        return self.end is not None

    def unbounded(self) -> bool:
        return self.start is None and self.end is None

    def includes_start(self) -> bool:
        return (self.inclusivity & TimeRange.INCLUDE_START) != 0

    def includes_end(self) -> bool:
        return (self.inclusivity & TimeRange.INCLUDE_END) != 0

    def finite(self) -> bool:
        return (self.start is not None and self.end is not None)

    def __contains__(self, ts: object) -> bool:
        """Returns true if the timestamp is within this range."""
        return ((isinstance(ts, SupportsMediaTimeOffset)) and
                (self.start is None or mediatimeoffset(ts) >= self.start) and
                (self.end is None or mediatimeoffset(ts) <= self.end) and
                (not ((self.start is not None) and
                      (mediatimeoffset(ts) == self.start) and
                      (self.inclusivity & TimeRange.INCLUDE_START == 0))) and
                (not ((self.end is not None) and
                      (mediatimeoffset(ts) == self.end) and
                      (self.inclusivity & TimeRange.INCLUDE_END == 0))))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SupportsMediaTimeRange):
            return False

        other = mediatimerange(other)
        return (isinstance(other, SupportsMediaTimeRange) and
                ((self.is_empty() and other.is_empty()) or
                (((self.start is None and other.start is None) or
                  (self.start == other.start and
                   (self.inclusivity & TimeRange.INCLUDE_START) == (other.inclusivity & TimeRange.INCLUDE_START))) and
                 ((self.end is None and other.end is None) or
                  (self.end == other.end and
                   (self.inclusivity & TimeRange.INCLUDE_END) == (other.inclusivity & TimeRange.INCLUDE_END))))))

    def __repr__(self) -> str:
        return "{}.{}.from_str('{}')".format("mediatimestamp.immutable", type(self).__name__, self.to_sec_nsec_range())

    def contains_subrange(self, tr: SupportsMediaTimeRange) -> bool:
        """Returns True if the timerange supplied lies entirely inside this timerange"""
        tr = mediatimerange(tr)
        return ((not self.is_empty()) and
                (tr.is_empty() or
                 (self.start is None or (tr.start is not None and self.start <= tr.start)) and
                 (self.end is None or (tr.end is not None and self.end >= tr.end)) and
                 (not ((self.start is not None) and
                       (tr.start is not None) and
                       (self.start == tr.start) and
                       (self.inclusivity & TimeRange.INCLUDE_START == 0) and
                       (tr.inclusivity & TimeRange.INCLUDE_START != 0))) and
                 (not ((self.end is not None) and
                       (tr.end is not None) and
                       (self.end == tr.end) and
                       (self.inclusivity & TimeRange.INCLUDE_END == 0) and
                       (tr.inclusivity & TimeRange.INCLUDE_END != 0)))))

    def to_sec_nsec_range(self, with_inclusivity_markers: bool = True) -> str:
        """Convert to [<seconds>:<nanoseconds>_<seconds>:<nanoseconds>] format,
        usually the opening and closing delimiters are set to [ or ] for inclusive and ( or ) for exclusive ranges.
        Unbounded ranges have no marker attached to them.

        :param with_inclusivity_markers: if set to False do not include parentheses/brackets"""
        if self.is_empty():
            if with_inclusivity_markers:
                return "()"
            else:
                return ""
        elif self.start is not None and self.end is not None and self.start == self.end:
            if with_inclusivity_markers:
                return "[" + self.start.to_tai_sec_nsec() + "]"
            else:
                return self.start.to_tai_sec_nsec()

        if with_inclusivity_markers:
            brackets = [("(", ")"), ("[", ")"), ("(", "]"), ("[", "]")][self.inclusivity]
        else:
            brackets = ("", "")

        return '_'.join([
            (brackets[0] + self.start.to_tai_sec_nsec()) if self.start is not None else '',
            (self.end.to_tai_sec_nsec() + brackets[1]) if self.end is not None else ''
            ])

    def intersect_with(self, tr: SupportsMediaTimeRange) -> "TimeRange":
        """Return a range which represents the intersection of this range with another"""
        tr = mediatimerange(tr)
        if self.is_empty() or tr.is_empty():
            return TimeRange.never()

        start = self.start
        if tr.start is not None and (self.start is None or self.start < tr.start):
            start = tr.start
        end = self.end
        if tr.end is not None and (self.end is None or self.end > tr.end):
            end = tr.end

        inclusivity = TimeRange.EXCLUSIVE
        if start is None or (start in self and start in tr):
            inclusivity |= TimeRange.INCLUDE_START
        if end is None or (end in self and end in tr):
            inclusivity |= TimeRange.INCLUDE_END

        if start is not None and end is not None and start > end:
            return TimeRange.never()

        return TimeRange(start, end, inclusivity)

    def starts_inside_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if the start of this timerange is located inside the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                ((self.bounded_before() and self.start in other and
                  (not (other.bounded_after() and self.start == other.end and not self.includes_start()))) or
                 (self.bounded_before() and other.bounded_before() and self.start == other.start and
                  (not (self.includes_start() and not other.includes_start()))) or
                 (not self.bounded_before() and not other.bounded_before())))

    def ends_inside_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if the end of this timerange is located inside the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                ((self.bounded_after() and self.end in other and
                  (not (other.bounded_before() and self.end == other.start and not self.includes_end()))) or
                 (self.bounded_after() and other.bounded_after() and self.end == other.end and
                  (not (self.includes_end() and not other.includes_end()))) or
                 (not self.bounded_after() and not other.bounded_after())))

    def is_earlier_than_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange ends earlier than the start of the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_before() and
                self.bounded_after() and
                (cast(Timestamp, self.end) < cast(Timestamp, other.start) or
                 (cast(Timestamp, self.end) == cast(Timestamp, other.start) and
                  not (self.includes_end() and other.includes_start()))))

    def is_later_than_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange starts later than the end of the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_after() and
                self.bounded_before() and
                (cast(Timestamp, self.start) > cast(Timestamp, other.end) or
                 (cast(Timestamp, self.start) == cast(Timestamp, other.end) and
                  not (self.includes_start() and other.includes_end()))))

    def starts_earlier_than_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange starts earlier than the start of the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_before() and
                (not self.bounded_before() or
                 (cast(Timestamp, self.start) < cast(Timestamp, other.start) or
                  (cast(Timestamp, self.start) == cast(Timestamp, other.start) and
                   self.includes_start() and
                   not other.includes_start()))))

    def starts_later_than_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange starts later than the start of the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                self.bounded_before() and
                (not other.bounded_before() or
                 (cast(Timestamp, self.start) > cast(Timestamp, other.start) or
                  (cast(Timestamp, self.start) == cast(Timestamp, other.start) and
                   (not self.includes_start() and other.includes_start())))))

    def ends_earlier_than_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange ends earlier than the end of the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                self.bounded_after() and
                (not other.bounded_after() or
                 (cast(Timestamp, self.end) < cast(Timestamp, other.end) or
                  (cast(Timestamp, self.end) == cast(Timestamp, other.end) and
                   (not self.includes_end() and other.includes_end())))))

    def ends_later_than_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange ends later than the end of the other."""
        other = mediatimerange(other)
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_after() and
                (not self.bounded_after() or
                 (cast(Timestamp, self.end) > cast(Timestamp, other.end) or
                  (cast(Timestamp, self.end) == cast(Timestamp, other.end) and
                   self.includes_end() and
                   not other.includes_end()))))

    def overlaps_with_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if this timerange and the other overlap."""
        other = mediatimerange(other)
        return (not self.is_earlier_than_timerange(other) and not self.is_later_than_timerange(other))

    def is_contiguous_with_timerange(self, other: SupportsMediaTimeRange) -> bool:
        """Returns true if the union of this timerange and the other would be a valid timerange"""
        other = mediatimerange(other)
        return (self.overlaps_with_timerange(other) or
                (self.is_earlier_than_timerange(other) and
                 self.end == other.start and
                 (self.includes_end() or other.includes_start())) or
                (self.is_later_than_timerange(other) and
                 self.start == other.end and
                 (self.includes_start() or other.includes_end())))

    def union_with_timerange(self, other: SupportsMediaTimeRange) -> "TimeRange":
        """Returns the union of this timerange and the other.
        :raises: ValueError if the ranges are not contiguous."""
        other = mediatimerange(other)
        if not self.is_contiguous_with_timerange(other):
            raise ValueError("Timeranges {} and {} are not contiguous, so cannot take the union.".format(self, other))

        return self.extend_to_encompass_timerange(other)

    def extend_to_encompass_timerange(self, other: SupportsMediaTimeRange) -> "TimeRange":
        """Returns the timerange that encompasses this and the other timerange."""
        other = mediatimerange(other)
        if self.is_empty():
            return other

        if other.is_empty():
            return self

        inclusivity = TimeRange.EXCLUSIVE
        if self.start == other.start:
            start = self.start
            inclusivity |= ((self.inclusivity | other.inclusivity) & TimeRange.INCLUDE_START)
        elif self.starts_earlier_than_timerange(other):
            start = self.start
            inclusivity |= (self.inclusivity & TimeRange.INCLUDE_START)
        else:
            start = other.start
            inclusivity |= (other.inclusivity & TimeRange.INCLUDE_START)

        if self.end == other.end:
            end = self.end
            inclusivity |= ((self.inclusivity | other.inclusivity) & TimeRange.INCLUDE_END)
        elif self.ends_later_than_timerange(other):
            end = self.end
            inclusivity |= (self.inclusivity & TimeRange.INCLUDE_END)
        else:
            end = other.end
            inclusivity |= (other.inclusivity & TimeRange.INCLUDE_END)

        return TimeRange(start, end, inclusivity)

    def split_at(self, timestamp: SupportsMediaTimestamp) -> Tuple["TimeRange", "TimeRange"]:
        """Splits a timerange at a specified timestamp.

        It is guaranteed that the splitting point will be in the *second* TimeRange returned, and not in the first.

        :param timestamp: the timestamp to split at
        :returns: A pair of TimeRange objects
        :raises: ValueError if timestamp not in self"""

        timestamp = mediatimestamp(timestamp)

        if timestamp not in self:
            raise ValueError("Cannot split range {} at {}".format(self, timestamp))

        return (TimeRange(self.start, timestamp, (self.inclusivity & TimeRange.INCLUDE_START)),
                TimeRange(timestamp, self.end, TimeRange.INCLUDE_START | (self.inclusivity & TimeRange.INCLUDE_END)))

    def timerange_between(self, other: SupportsMediaTimeRange) -> "TimeRange":
        """Returns the time range between the end of the earlier timerange and the start of the later one"""
        other = mediatimerange(other)

        if self.is_contiguous_with_timerange(other):
            return TimeRange.never()
        elif self.is_earlier_than_timerange(other):
            inclusivity = TimeRange.EXCLUSIVE
            if not self.includes_end():
                inclusivity |= TimeRange.INCLUDE_START
            if not other.includes_start():
                inclusivity |= TimeRange.INCLUDE_END
            return TimeRange(self.end, other.start, inclusivity)
        else:
            inclusivity = TimeRange.EXCLUSIVE
            if not self.includes_start():
                inclusivity |= TimeRange.INCLUDE_END
            if not other.includes_end():
                inclusivity |= TimeRange.INCLUDE_START
            return TimeRange(other.end, self.start, inclusivity)

    def is_empty(self) -> bool:
        """Returns true on any empty range."""
        return (self.start is not None and
                self.end is not None and
                self.start == self.end and
                self.inclusivity != TimeRange.INCLUSIVE)

    def normalise(self,
                  rate_num: RationalTypes,
                  rate_den: RationalTypes = 1,
                  rounding: Rounding = ROUND_NEAREST) -> "TimeRange":
        """Returns a normalised half-open TimeRange based on this timerange.

        The returned TimeRange will always have INCLUDE_START inclusivity.

        If the original TimeRange was inclusive of its start then the returned TimeRange will
        start at the normalised timestamp closest to that start point (respecting rounding).

        If the original TimeRange was exclusive of its start then the returned TimeRange will
        start at the next normalised timestamp after the normalised timestamp closest to that
        start point (respecting rounding).

        If the original TimeRange was exclusive of its end then the returned TimeRange will
        end just before the normalised timestamp closest to that end point (respecting rounding).

        If the original TimeRange was inclusive of its end then the returned TimeRange will
        end just before the next normalised timestamp after the normalised timestamp closest to that
        end point (respecting rounding).

        The rounding options are:
        * ROUND_NEAREST -- each end of the range independently rounds to the nearest normalised timestamp
        * ROUND_UP -- both ends of the range round up
        * ROUND_DOWN -- both ends of the range round down
        * ROUND_IN -- The start of the range rounds up, the end rounds down
        * ROUND_OUT -- The start of the range rounds down, the end rounds up
        * ROUND_START -- The start rounds to the nearest normalised timestamp, the end rounds in the same direction
                         as the start
        * ROUND_END -- The end rounds to the nearest normalised timestamp, the start rounds in the same direction
                       as the end
        """
        if rounding == TimeRange.ROUND_OUT:
            start_rounding = Timestamp.ROUND_DOWN
            end_rounding = Timestamp.ROUND_UP
        elif rounding == TimeRange.ROUND_IN:
            start_rounding = Timestamp.ROUND_UP
            end_rounding = Timestamp.ROUND_DOWN
        elif rounding in [TimeRange.ROUND_START, TimeRange.ROUND_END]:
            start_rounding = Timestamp.ROUND_NEAREST
            end_rounding = Timestamp.ROUND_NEAREST
        else:
            start_rounding = Timestamp.Rounding(rounding)
            end_rounding = Timestamp.Rounding(rounding)

        rate = Fraction(rate_num, rate_den)

        start: Optional[int]
        if self.bounded_before():
            start = cast(Timestamp, self.start).to_count(rate, rounding=start_rounding)
        else:
            start = None

        end: Optional[int]
        if self.bounded_after():
            end = cast(Timestamp, self.end).to_count(rate, rounding=end_rounding)
        else:
            end = None

        if rounding == TimeRange.ROUND_START and self.bounded_before() and self.bounded_after():
            if start == cast(Timestamp, self.start).to_count(rate, rounding=Timestamp.ROUND_UP):
                end = cast(Timestamp, self.end).to_count(rate, rounding=Timestamp.ROUND_UP)
            else:
                end = cast(Timestamp, self.end).to_count(rate, rounding=Timestamp.ROUND_DOWN)
        elif rounding == TimeRange.ROUND_END and self.bounded_before() and self.bounded_after():
            if end == cast(Timestamp, self.end).to_count(rate, rounding=Timestamp.ROUND_UP):
                start = cast(Timestamp, self.start).to_count(rate, rounding=Timestamp.ROUND_UP)
            else:
                start = cast(Timestamp, self.start).to_count(rate, rounding=Timestamp.ROUND_DOWN)

        if start is not None and not self.includes_start():
            start += 1
        if end is not None and self.includes_end():
            end += 1

        start_ts: Optional[Timestamp] = None
        end_ts: Optional[Timestamp] = None
        if start is not None:
            start_ts = Timestamp.from_count(start, rate)
        if end is not None:
            end_ts = Timestamp.from_count(end, rate)

        return TimeRange(start_ts,
                         end_ts,
                         TimeRange.INCLUDE_START)
