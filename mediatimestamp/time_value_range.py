# Copyright 2019 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

from typing import Optional, Union, Any, Tuple, Iterator, Reversible, cast, Iterable
import re
from fractions import Fraction

from .immutable import (
    SupportsMediaTimestamp,
    TimeOffset, SupportsMediaTimeOffset,
    TimeRange, SupportsMediaTimeRange, mediatimerange)

from .count_range import CountRange
from .time_value import TimeValue
from .time_value import TimeValueConstructTypes, _perform_all_conversions


RangeTypes = Union[TimeRange, CountRange, "TimeValueRange"]
RangeConstructionTypes = Union[SupportsMediaTimeRange, RangeTypes]


class TimeValueRange(Reversible[TimeValue]):
    """Represents a range of media unit time values on a timeline (e.g. Flow).

    Supports these range types if start_or_value is a range value:
    * TimeRange
    * CountRange
    * TimeValueRange
    * Anything that implements the __mediatimerange__ magic method, but does not implement the __mediatimestamp__ or
      __mediatimeoffset__ magic methods.

    Supports one of the following time value constructor representations if start_or_value is a range start:
    * TimeOffset
    * Timestamp
    * int (integer media unit count)
    * TimeValue
    * Anything that implements the __mediatimestamp__ magic method
    * Anything that implements the __mediatimeoffset__ magic method

    If state_or_value could be interpreted as a range value without

    An optional rate can be set and is required and checked when there is a
    need to convert between representations.

    The time value range can be converted to a TimeRange or CountRange using
    the as_*() methods.

    The time value range implements the __mediatimerange__ magic method.
    """

    # These inclusivity and rounding values must match the TimeRange values

    EXCLUSIVE = 0x0
    INCLUDE_START = 0x1
    INCLUDE_END = 0x2
    INCLUSIVE = 0x3

    ROUND_DOWN = 0
    ROUND_NEAREST = 1
    ROUND_UP = 2
    ROUND_IN = 3
    ROUND_OUT = 4
    ROUND_START = 5
    ROUND_END = 6

    def __init__(self, start_or_value: Optional[Union[TimeValueConstructTypes, RangeConstructionTypes]],
                 end: Optional[TimeValueConstructTypes] = None,
                 inclusivity: Optional[int] = None,
                 rate: Optional[Fraction] = None,
                 *,
                 start: Optional[TimeValueConstructTypes] = None,
                 value: Optional[RangeConstructionTypes] = None):
        """Construct a time value range

        :param start_or_value: The start of the range, a range or None
        :param end: The end of the range or None
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END
        :param rate: The media unit rate.
        """
        self_start: Optional[TimeValue]
        self_end: Optional[TimeValue]
        self_rate: Optional[Fraction] = rate

        if value is None and (
            isinstance(start_or_value, (TimeValueRange, TimeRange, CountRange)) or
            (
                not isinstance(start_or_value, (SupportsMediaTimestamp, SupportsMediaTimeOffset)) and
                isinstance(start_or_value, SupportsMediaTimeRange)
            )
        ):
            value = start_or_value

        if isinstance(value, (TimeValueRange, TimeRange, CountRange)):
            start = value.start
            end = value.end
            self_inclusivity = inclusivity if inclusivity is not None else value.inclusivity
        elif (
            not isinstance(range, (SupportsMediaTimestamp, SupportsMediaTimeOffset)) and
            isinstance(range, SupportsMediaTimeRange)
        ):
            value = mediatimerange(value)
            start = value.start
            end = value.end
            self_inclusivity = inclusivity if inclusivity is not None else value.inclusivity
        else:
            if start_or_value is not None:
                if not isinstance(start_or_value, (SupportsMediaTimeOffset, SupportsMediaTimestamp, int, TimeValue)):
                    raise ValueError(f"Unsupported type for start: {start_or_value!r}")
                if start is not None:
                    raise ValueError("Cannot specify start or value as a positional and a keyword parameter!")
                start = start_or_value
            self_inclusivity = inclusivity if inclusivity is not None else TimeValueRange.INCLUSIVE

        if start is not None:
            self_start = TimeValue(start, rate=self_rate)
            self_rate = self_start._rate
        else:
            self_start = None

        if end is not None:
            self_end = TimeValue(end, rate=self_rate)
            self_rate = self_end._rate
        else:
            self_end = None

        # Add a rate to the start if it was available in end
        if self_rate and self_start is not None:
            self_start = TimeValue(self_start, rate=self_rate)

        # normalise the representation to always have an inclusive start if bounded
        if self_start is not None and (
                (self_rate or isinstance(self_start.value, int)) and
                not (self_inclusivity & TimeValueRange.INCLUDE_START)):
            self_start = self_start + 1
            self_inclusivity |= TimeValueRange.INCLUDE_START

        # normalise the representation to always have an exclusive end if bounded
        if self_end is not None and (
                (self_rate or isinstance(self_end.value, int)) and
                (self_inclusivity & TimeValueRange.INCLUDE_END)):
            self_end = self_end + 1
            self_inclusivity &= ~TimeValueRange.INCLUDE_END

        # Normalise the 'never' cases
        if self_start is not None and self_end is not None:
            if self_start > self_end or (self_start == self_end and self_inclusivity != TimeValueRange.INCLUSIVE):
                self_start = TimeValue(0, self_rate)
                self_end = TimeValue(0, self_rate)
                self_inclusivity = TimeValueRange.EXCLUSIVE

        # Normalise the 'eternity' cases
        if self_start is None and self_end is None:
            self_inclusivity = TimeValueRange.INCLUSIVE

        # set attributes using dict to workaround immutability
        self.__dict__['_start'] = self_start
        self.__dict__['_end'] = self_end
        self.__dict__['_inclusivity'] = self_inclusivity
        self.__dict__['_rate'] = self_rate

        # provide attribute type info given that attributes are not set directly
        self._start: Optional[TimeValue]
        self._end: Optional[TimeValue]
        self._inclusivity: int
        self._rate: Optional[Fraction]

    @classmethod
    def from_start(cls, start: TimeValueConstructTypes,
                   inclusivity: int = INCLUSIVE,
                   rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Construct a range starting at start with no end

        :param start: A time value or type supported by TimeValue
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END
        :param rate: The media unit rate."""
        return cls(start, None, inclusivity=inclusivity, rate=rate)

    @classmethod
    def from_end(cls, end: TimeValueConstructTypes,
                 inclusivity: int = INCLUSIVE,
                 rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Construct a range ending at end with no start

        :param end: A time value or type supported by TimeValue
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END
        :param rate: The media unit rate."""
        return cls(None, end, inclusivity=inclusivity, rate=rate)

    @classmethod
    def from_start_length(cls, start: TimeValueConstructTypes,
                          length: TimeValueConstructTypes,
                          inclusivity: int = INCLUSIVE,
                          rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Construct a range starting at start and ending at (start + length)

        :param start: A time value or type supported by TimeValue
        :param length: A time value or type supported by TimeValue, which must be non-negative
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END
        :param rate: The media unit rate.

        :raises: ValueError if the length is negative"""
        length = _perform_all_conversions(length)
        if length < 0:
            raise ValueError("Length must be non-negative")

        end = TimeValue(start, rate=rate) + length
        return cls(start, end, inclusivity=inclusivity, rate=rate)

    @classmethod
    def eternity(cls, rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Return an unbounded range covering all time"""
        return cls(None, None, rate=rate)

    @classmethod
    def never(cls, rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Return a range covering no time

        :param rate: The media unit rate."""
        return cls(TimeValue(0), TimeValue(0), inclusivity=TimeValueRange.EXCLUSIVE, rate=rate)

    @classmethod
    def from_single_value(cls, value: TimeValueConstructTypes,
                          rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Construct a range containing only a single time value

        :param value: A time value or type supported by TimeValue
        :param rate: The media unit rate."""
        return cls(value, value, inclusivity=TimeValueRange.INCLUSIVE, rate=rate)

    @classmethod
    def from_str(cls, s: str, rate: Optional[Fraction] = None) -> "TimeValueRange":
        """Convert a string to a range.

        Valid ranges are:
        [<tv>_<tv>]
        [<tv>_<tv>)
        (<tv>_<tv>]
        (<tv>_<tv>)
        [<tv>]
        <tv>_<tv>
        <tv>
        ()

        where <tv> is an integer or an empty string.

        The meaning of these is relatively simple: [ indicates including the start time value,
        ( indicates excluding it, ] indicates including the end time value, and ) indicates excluding it.
        If brackets are ommitted entirely then this is taken as an inclusive range at both ends.
        Omitting a time value indicates that there is no bound on that end (ie. the range goes on forever),
        including only a single time value by itself indicates a range containing exactly that one time value.
        Finally the string "()" represents the empty range.

        :param s: The string to process
        :param rate: The media unit rate.
        """
        m = re.match(r'(\[|\()?([^_\)\]]+)?(_([^_\)\]]+)?)?(\]|\))?(@([^\/]+(\/.+)?))?', s)

        if m is None:
            raise ValueError("Invalid TimeValueRange string")

        inc = TimeValueRange.INCLUSIVE
        if m.group(1) == "(":
            inc &= ~TimeValueRange.INCLUDE_START
        if m.group(5) == ")":
            inc &= ~TimeValueRange.INCLUDE_END

        start_str = m.group(2)
        end_str = m.group(4)
        rate_str = m.group(7)

        if rate is None and rate_str is not None:
            rate = Fraction(rate_str)

        if start_str is not None:
            start = TimeValue.from_str(start_str, rate=rate)
        else:
            start = None
        if end_str is not None:
            end = TimeValue.from_str(end_str, rate=rate)
        else:
            end = None

        if start is None and end is None:
            # Ie. we have no first or second value
            if m.group(3) is not None:
                # ie. we have a '_' character
                return cls.eternity()
            else:
                # We have no '_' character, so the whole range is empty
                return cls.never()
        elif start is not None and end is None and m.group(3) is None:
            return cls.from_single_value(start)
        else:
            return cls(start, end, inclusivity=inc, rate=rate)

    def as_timerange(self) -> TimeRange:
        """Returns a TimeRange representation."""
        start = self._start.as_timestamp() if self._start is not None else None
        end = self._end.as_timestamp() if self._end is not None else None
        inclusivity = self._inclusivity
        return TimeRange(start, end, inclusivity=TimeRange.Inclusivity(inclusivity))

    def __mediatimerange__(self) -> TimeRange:
        return self.as_timerange()

    def as_count_range(self) -> CountRange:
        """Returns a CountRange representation."""
        start = self._start.as_count() if self._start is not None else None
        end = self._end.as_count() if self._end is not None else None
        inclusivity = self._inclusivity
        return CountRange(start, end, inclusivity=inclusivity)

    @property
    def start(self) -> Optional[TimeValue]:
        return self._start

    @property
    def end(self) -> Optional[TimeValue]:
        return self._end

    @property
    def inclusivity(self) -> int:
        return self._inclusivity

    @property
    def rate(self) -> Optional[Fraction]:
        return self._rate

    def length_as_timeoffset(self) -> Union[TimeOffset, float]:
        """Returns the range length as a TimeOffset or the float value infinity"""
        return self.as_timerange().length

    def length_as_count(self) -> Union[int, float]:
        """Returns the range length as an media unit count"""
        return self.as_count_range().length

    def bounded_before(self) -> bool:
        """Return true if the start of the range is bounded"""
        return self._start is not None

    def bounded_after(self) -> bool:
        """Return true if the end of the range is bounded"""
        return self._end is not None

    def unbounded(self) -> bool:
        """Return true if neither the start or end of the range is bounded"""
        return self._start is None and self._end is None

    def includes_start(self) -> bool:
        """Return true if the start is inclusive"""
        return (self._inclusivity & TimeValueRange.INCLUDE_START) != 0

    def includes_end(self) -> bool:
        """Return true if the end is inclusive"""
        return (self._inclusivity & TimeValueRange.INCLUDE_END) != 0

    def finite(self) -> bool:
        """Return true if the range is finite"""
        return (self._start is not None and self._end is not None)

    def contains_subrange(self, other: RangeConstructionTypes) -> bool:
        """Returns true if the range supplied lies entirely inside this range"""
        other = self._as_time_value_range(other)

        return ((not self.is_empty()) and
                (other.is_empty() or
                 (self._start is None or (other._start is not None and self._start <= other._start)) and
                 (self._end is None or (other._end is not None and self._end >= other._end)) and
                 (not ((self._start is not None) and
                       (other._start is not None) and
                       (self._start == other._start) and
                       (self._inclusivity & TimeValueRange.INCLUDE_START == 0) and
                       (other._inclusivity & TimeValueRange.INCLUDE_START != 0))) and
                 (not ((self._end is not None) and
                       (other._end is not None) and
                       (self._end == other._end) and
                       (self._inclusivity & TimeValueRange.INCLUDE_END == 0) and
                       (other._inclusivity & TimeValueRange.INCLUDE_END != 0)))))

    def to_str(self, with_inclusivity_markers: bool = True,
               include_rate: bool = True) -> str:
        """Convert to [<value>_<value>] format,
        usually the opening and closing delimiters are set to [ or ] for inclusive and ( or ) for exclusive ranges.
        Unbounded ranges have no marker attached to them.

        :param with_inclusivity_markers: if set to False do not include parentheses/brackecount
        :param include_rate: If True and there is a non-zero media rate then include the media rate suffix string
        """
        if self.is_empty():
            if with_inclusivity_markers:
                return "()"
            else:
                return ""
        elif self._start is not None and self._end is not None and self._start == self._end:
            if with_inclusivity_markers:
                return "[" + self._start.to_str(False) + "]"
            else:
                return self._start.to_str(False)

        if with_inclusivity_markers:
            brackets = [("(", ")"), ("[", ")"), ("(", "]"), ("[", "]")][self._inclusivity]
        else:
            brackets = ("", "")

        result = '_'.join([
            (brackets[0] + self._start.to_str(False)) if self._start is not None else '',
            (self._end.to_str(False) + brackets[1]) if self._end is not None else ''
            ])
        if include_rate and self._rate:
            result += "@{}".format(self._rate)
        return result

    def intersect_with(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Return a range which represents the intersection of this range with another"""
        other = self._as_time_value_range(other)

        if self.is_empty() or other.is_empty():
            return TimeValueRange.never()

        start = self._start
        if other._start is not None and (self._start is None or self._start < other._start):
            start = other._start
        end = self._end
        if other._end is not None and (self._end is None or self._end > other._end):
            end = other._end

        inclusivity = TimeValueRange.EXCLUSIVE
        if start is None or (start in self and start in other):
            inclusivity |= TimeValueRange.INCLUDE_START
        if end is None or (end in self and end in other):
            inclusivity |= TimeValueRange.INCLUDE_END

        if start is not None and end is not None and start > end:
            return TimeValueRange.never()

        return TimeValueRange(start, end, inclusivity)

    def starts_inside_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if the start of this range is located inside the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                ((self.bounded_before() and cast(TimeValue, self._start) in other and
                  (not (other.bounded_after() and self._start == other._end and not self.includes_start()))) or
                 (self.bounded_before() and other.bounded_before() and self._start == other._start and
                  (not (self.includes_start() and not other.includes_start()))) or
                 (not self.bounded_before() and not other.bounded_before())))

    def ends_inside_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if the end of this range is located inside the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                ((self.bounded_after() and cast(TimeValue, self._end) in other and
                  (not (other.bounded_before() and self._end == other._start and not self.includes_end()))) or
                 (self.bounded_after() and other.bounded_after() and self._end == other._end and
                  (not (self.includes_end() and not other.includes_end()))) or
                 (not self.bounded_after() and not other.bounded_after())))

    def is_earlier_than_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range ends earlier than the start of the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                (other.bounded_before() and
                    other._start is not None) and  # redundant but is for type checking
                (self.bounded_after() and
                    self._end is not None) and  # redundant but is for type checking
                (self._end < other._start or
                 (self._end == other._start and
                  not (self.includes_end() and other.includes_start()))))

    def is_later_than_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range starts later than the end of the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                (other.bounded_after() and
                    other._end is not None) and  # redundant but is for type checking
                (self.bounded_before() and
                    self._start is not None) and  # redundant but is for type checking
                (self._start > other._end or
                 (self._start == other._end and
                  not (self.includes_start() and other.includes_end()))))

    def starts_earlier_than_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range starts earlier than the start of the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                (other.bounded_before() and
                    other._start is not None) and  # redundant but is for type checking
                ((not self.bounded_before() or
                    self._start is None) or  # redundant but is for type checking
                 (self._start < other._start or
                  (self._start == other._start and
                   self.includes_start() and
                   not other.includes_start()))))

    def starts_later_than_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range starts later than the start of the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                (self.bounded_before() and
                    self._start is not None) and  # redundant but is for type checking
                ((not other.bounded_before() or
                    other._start is None) or  # redundant but is for type checking
                 (self._start > other._start or
                  (self._start == other._start and
                   (not self.includes_start() and other.includes_start())))))

    def ends_earlier_than_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range ends earlier than the end of the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                (self.bounded_after() and
                    self._end is not None) and  # redundant but is for type checking
                ((not other.bounded_after() or
                    other._end is None) or  # redundant but is for type checking
                 (self._end < other._end or
                  (self._end == other._end and
                   (not self.includes_end() and other.includes_end())))))

    def ends_later_than_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range ends later than the end of the other."""
        other = self._as_time_value_range(other)

        return (not self.is_empty() and
                not other.is_empty() and
                (other.bounded_after() and
                    other._end is not None) and  # redundant but is for type checking
                ((not self.bounded_after() or
                    self._end is None) or  # redundant but is for type checking
                 (self._end > other._end or
                  (self._end == other._end and
                   self.includes_end() and
                   not other.includes_end()))))

    def overlaps_with_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if this range and the other overlap."""
        other = self._as_time_value_range(other)

        return (not self.is_earlier_than_range(other) and not self.is_later_than_range(other))

    def is_contiguous_with_range(self, other: RangeConstructionTypes) -> bool:
        """Returns true if the union of this range and the other would be a valid range"""
        other = self._as_time_value_range(other)

        return (self.overlaps_with_range(other) or
                (self.is_earlier_than_range(other) and
                 self._end == other._start and
                 (self.includes_end() or other.includes_start())) or
                (self.is_later_than_range(other) and
                 self._start == other._end and
                 (self.includes_start() or other.includes_end())))

    def union_with_range(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Returns the union of this range and the other.
        :raises: ValueError if the ranges are not contiguous."""
        other = self._as_time_value_range(other)

        if not self.is_contiguous_with_range(other):
            raise ValueError("TimeValueRanges {} and {} are not contiguous, so cannot take the union.".format(
                             self, other))

        return self.extend_to_encompass_range(other)

    def extend_to_encompass_range(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Returns the range that encompasses this and the other range."""
        other = self._as_time_value_range(other)

        if self.is_empty():
            return other

        if other.is_empty():
            return self

        inclusivity = TimeValueRange.EXCLUSIVE
        if self._start == other._start:
            start = self._start
            inclusivity |= ((self._inclusivity | other._inclusivity) & TimeValueRange.INCLUDE_START)
        elif self.starts_earlier_than_range(other):
            start = self._start
            inclusivity |= (self._inclusivity & TimeValueRange.INCLUDE_START)
        else:
            start = other._start
            inclusivity |= (other._inclusivity & TimeValueRange.INCLUDE_START)

        if self._end == other._end:
            end = self._end
            inclusivity |= ((self._inclusivity | other._inclusivity) & TimeValueRange.INCLUDE_END)
        elif self.ends_later_than_range(other):
            end = self._end
            inclusivity |= (self._inclusivity & TimeValueRange.INCLUDE_END)
        else:
            end = other._end
            inclusivity |= (other._inclusivity & TimeValueRange.INCLUDE_END)

        return TimeValueRange(start, end, inclusivity)

    def split_at(self, value: TimeValueConstructTypes) -> Tuple["TimeValueRange", "TimeValueRange"]:
        """Splits a range at a specified value.

        It is guaranteed that the splitting point will be in the *second* TimeValueRange returned, and not in the first.

        :param value: the time value to split at
        :returns: A pair of TimeValueRange objects
        :raises: ValueError if value not in self"""
        value = self._as_time_value(value)

        if value not in self:
            raise ValueError("Cannot split range {} at {}".format(self, value))

        return (TimeValueRange(self._start,
                               value,
                               (self._inclusivity & TimeValueRange.INCLUDE_START)),
                TimeValueRange(value,
                               self._end,
                               TimeValueRange.INCLUDE_START | (self._inclusivity & TimeValueRange.INCLUDE_END)))

    def split_after(self, value: TimeValueConstructTypes) -> Tuple["TimeValueRange", "TimeValueRange"]:
        """Splits a range after a specified value.

        It is guaranteed that the splitting point will be in the *first* TimeValueRange returned, and not in the second.

        :param value: the time value to split at
        :returns: A pair of TimeValueRange objects
        :raises: ValueError if value not in self"""
        value = self._as_time_value(value)

        if value not in self:
            raise ValueError("Cannot split range {} at {}".format(self, value))

        return (TimeValueRange(self._start,
                               value,
                               TimeValueRange.INCLUDE_END | (self._inclusivity & TimeValueRange.INCLUDE_START)),
                TimeValueRange(value,
                               self._end,
                               (self._inclusivity & TimeValueRange.INCLUDE_END)))

    def excluding_up_to_end_of_range(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Returns the portion of this timerange which is not earlier than or contained in the
        given timerange.
        """
        other = self._as_time_value_range(other)

        if other.is_empty() or other.is_earlier_than_range(self):
            return self
        elif not other.bounded_after() or cast(TimeValue, other.end) not in self:
            return TimeValueRange.never()
        else:
            if other.includes_end():
                return self.split_after(cast(TimeValue, other.end))[1]
            else:
                return self.split_at(cast(TimeValue, other.end))[1]

    def excluding_before_start_of_range(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Returns the portion of this timerange which is not later than or contained in the
        given timerange.
        """
        other = self._as_time_value_range(other)

        if other.is_empty() or other.is_later_than_range(self):
            return self
        elif not other.bounded_before() or cast(TimeValue, other.start) not in self:
            return TimeValueRange.never()
        else:
            assert(isinstance(other.start, TimeValue))
            if other.includes_start():
                return self.split_at(other.start)[0]
            else:
                return self.split_after(other.start)[0]

    def range_between(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Returns the range between the end of the earlier range and the start of the later one"""
        other = self._as_time_value_range(other)

        if self.is_contiguous_with_range(other):
            return TimeValueRange.never()
        elif self.is_earlier_than_range(other):
            inclusivity = TimeValueRange.EXCLUSIVE
            if not self.includes_end():
                inclusivity |= TimeValueRange.INCLUDE_START
            if not other.includes_start():
                inclusivity |= TimeValueRange.INCLUDE_END
            return TimeValueRange(self._end, other._start, inclusivity)
        else:
            inclusivity = TimeValueRange.EXCLUSIVE
            if not self.includes_start():
                inclusivity |= TimeValueRange.INCLUDE_END
            if not other.includes_end():
                inclusivity |= TimeValueRange.INCLUDE_START
            return TimeValueRange(other._end, self._start, inclusivity)

    def is_empty(self) -> bool:
        """Returns true on any empty range."""
        return (self._start is not None and
                self._end is not None and
                self._start == self._end and
                self._inclusivity != TimeValueRange.INCLUSIVE)

    def __setattr__(self, name: str, value: Any) -> None:
        """Raises a ValueError if attempt to set an attribute on the immutable TimeValueRange"""
        raise ValueError("Cannot assign to an immutable TimeValueRange")

    def __contains__(self, value: TimeValueConstructTypes) -> bool:
        """Returns true if the time value is within this range."""
        value = self._as_time_value(value)

        return ((self._start is None or value >= self._start) and
                (self._end is None or value <= self._end) and
                (not ((self._start is not None) and
                      (value == self._start) and
                      (self._inclusivity & TimeValueRange.INCLUDE_START == 0))) and
                (not ((self._end is not None) and
                      (value == self._end) and
                      (self._inclusivity & TimeValueRange.INCLUDE_END == 0))))

    def __eq__(self, other: object) -> bool:
        """Return true if the ranges are equal"""
        try:
            other = self._as_time_value_range(cast(RangeConstructionTypes, other))
        except Exception:
            return False

        return (((self.is_empty() and other.is_empty()) or
                (((self._start is None and other._start is None) or
                  (self._start == other._start and
                   (self._inclusivity & TimeValueRange.INCLUDE_START) == (other._inclusivity & TimeValueRange.INCLUDE_START))) and  # noqa: E501
                 ((self._end is None and other._end is None) or
                  (self._end == other._end and
                   (self._inclusivity & TimeValueRange.INCLUDE_END) == (other._inclusivity & TimeValueRange.INCLUDE_END))))))  # noqa: E501

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return "{}.{}.from_str('{}')".format(type(self).__module__, type(self).__name__, self.to_str())

    def _as_time_value(self, other: TimeValueConstructTypes) -> TimeValue:
        """Returns a TimeValue from `other`.

        A rate conversion is done if `other` is a TimeValue and the rate
        differs from self._rate.

        :param other: A TimeValue, TimeOffset, TimeStamp or int.
        """
        return TimeValue(other, rate=self._rate)

    def _as_time_value_range(self, other: RangeConstructionTypes) -> "TimeValueRange":
        """Returns a TimeValueRange from `other`.

        A rate conversion is done if `other` is a TimeValueRange and the rate
        differs from self._rate.

        :param other: A TimeValueRange, TimeRange or CountRange.
        """
        return TimeValueRange(other, rate=self._rate)

    def subranges(self, rate: Optional[Fraction] = None) -> Iterator["TimeValueRange"]:
        """Divide this range naturally into subranges.

        (nb. Ranges with a rate set are automatically normalised to half-open, which may lead
        to unexpected results when using this method with some ranges that have a rate but were
        not originally defined as half-open)

        If the rate parameter is specified then the boundaries between subranges will occur
        at that frequency through the range. If it is None then the rate of this range will
        be used instead if it has one. If this range has no rate then the returned iterable
        will yield only a single timerange, which is equal to this one.

        If this range is unbounded before then the iterable yields a single range equal to
        this one.

        Provided that this range is bounded before and a rate has been provided somehow, the
        first subrange yielded will have the same start clusivity as this range. If this range
        is bounded after then the last time range yielded will have the same end clusivity as
        this range. Any other timeranges yielded will be half-open (ie. INCLUDE_START). The
        yielded timeranges will be contiguous and non-overlapping. Every portion of this range
        will be covered by exactly one of the yielded ranges and all of the yielded ranges will
        be entirely contained within this range.

        :param rate: Optional rate.
        """
        _rate: Fraction
        if rate is None:
            if self.rate is None:
                return iter([self])
            else:
                _rate = self.rate
        else:
            _rate = rate

        if self.is_empty() or not self.bounded_before():
            return iter([self])

        def __inner():
            start: TimeValue = cast(TimeValue, self.start)
            include_start = self.includes_start()

            for tv in TimeValueRange(self, rate=_rate):
                if tv == start:
                    continue
                elif tv == self.end:
                    break
                else:
                    yield TimeValueRange(
                        start.as_timestamp(),
                        tv.as_timestamp(),
                        rate=self.rate,
                        inclusivity=TimeValueRange.INCLUDE_START if include_start else TimeValueRange.EXCLUSIVE)
                    include_start = True
                    start = tv

            inclusivity = TimeValueRange.EXCLUSIVE
            if include_start:
                inclusivity |= TimeValueRange.INCLUDE_START
            if self.includes_end():
                inclusivity |= TimeValueRange.INCLUDE_END

            yield TimeValueRange(
                start.as_timestamp(),
                self.end.as_timestamp(),
                rate=self.rate,
                inclusivity=inclusivity)

        return __inner()

    def __iter__(self) -> Iterator[TimeValue]:
        """If this range has no rate set or is unbounded before then this will raise a ValueError.

        If this range has a rate then this returns an iterator which yields TimeValues contained
        within this range starting at the start of the range and moving forward at the range's rate.
        """
        if self.is_empty():
            return iter([])

        if not self.bounded_before() or self.rate is None:
            raise ValueError("{!r} is not iterable".format(self))

        first: TimeValue
        if self.includes_start():
            first = cast(TimeValue, self.start)
        else:
            first = cast(TimeValue, self.start) + 1

        last: Optional[TimeValue]
        if not self.bounded_after():
            last = None
        elif self.includes_end():
            last = cast(TimeValue, self.end)
        else:
            last = cast(TimeValue, self.end) - 1

        def __inner(first: TimeValue, last: Optional[TimeValue]) -> Iterator[TimeValue]:
            cur = first
            while last is None or cur <= last:
                yield cur
                cur = cur + 1

        return __inner(first, last)

    def __reversed__(self) -> Iterator[TimeValue]:
        """If this range has no rate set or is unbounded after then this will raise a ValueError.

        If this range has a rate then this returns an iterator which yields TimeValues contained
        within this range starting at the end of the range and moving backward at the range's rate.
        """
        if self.is_empty():
            return iter([])

        if not self.bounded_after() or self.rate is None:
            raise ValueError("reversed({!r}) is not iterable".format(self))

        first: TimeValue
        if self.includes_end():
            first = cast(TimeValue, self.end)
        else:
            first = cast(TimeValue, self.end) - 1

        last: Optional[TimeValue]
        if not self.bounded_before():
            last = None
        elif self.includes_start():
            last = cast(TimeValue, self.start)
        else:
            last = cast(TimeValue, self.start) + 1

        def __inner(first: TimeValue, last: Optional[TimeValue]) -> Iterator[TimeValue]:
            cur = first
            while last is None or cur >= last:
                yield cur
                cur = cur - 1

        return __inner(first, last)

    def __hash__(self) -> int:
        return hash(repr(self))

    def merge_into_ordered_ranges(self, ranges: Iterable["TimeValueRange"]) -> Iterable["TimeValueRange"]:
        """Merge this range into an ordered list of non-overlapping non-contiguous timeranges, returning the unique
        list of non-overlapping non-contiguous timeranges which covers the union of the ranges in the original list and
        also this timerange.

        :param ranges: An iterable yielding non-overlapping non-contiguous timeranges in chronological order
        :returns: An iterable yielding non-overlapping non-contiguous timeranges in chronological order"""
        new_range = self
        for existing_range in ranges:
            if ((existing_range.is_contiguous_with_range(new_range) or
                 existing_range.overlaps_with_range(new_range))):
                # This means that the new and old range can be combined together
                new_range = new_range.extend_to_encompass_range(existing_range)
            elif existing_range.is_earlier_than_range(new_range):
                # In this case the exiting range is entirely earlier than the new range and so won't interfere
                # with it
                yield existing_range
            elif existing_range.is_later_than_range(new_range):
                # The new_range is entirely located earlier than the existing range, we can simply add the
                # new_range
                yield new_range
                new_range = existing_range
        yield new_range

    def complement_of_ordered_subranges(self, ranges: Iterable["TimeValueRange"]) -> Iterable["TimeValueRange"]:
        """Given an iterable that yields chronologically ordered disjoint ranges yield chronologically ordered disjoint
        subranges of this range which cover every part of this range that is *not* covered by the input ranges.

        :param ranges: Iterable yielding chronologically ordered disjoint TimeValueRanges
        :returns: Iterable yielding chronologically ordered disjoint non-empty TimeValueRanges
        """
        current_timerange = self

        for existing_range in ranges:
            if not existing_range.is_empty():
                range_before = current_timerange.excluding_before_start_of_range(existing_range)
                if not range_before.is_empty():
                    yield range_before
                current_timerange = current_timerange.excluding_up_to_end_of_range(existing_range)

        if not current_timerange.is_empty():
            yield current_timerange
