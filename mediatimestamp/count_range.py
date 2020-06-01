# Copyright 2019 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

from typing import Optional, Union, Any, Tuple
import re


class CountRange(object):
    """Represents a range of integer media unit counts.

    The implementation matches mediatimestamp.immutable.TimeRange, but
    with Timestamps replaced with integer counts.
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

    def __init__(self, start: Optional[int],
                 end: Optional[int] = None,
                 inclusivity: int = INCLUSIVE):
        """Construct a count range starting at start and ending at end

        :param start: An integer media unit count or None
        :param end: An integer media unit count or None
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""

        # normalise the representation to always have an exclusive end if bounded
        if end is not None and (inclusivity & CountRange.INCLUDE_END):
            end = end + 1
            inclusivity &= ~CountRange.INCLUDE_END

        # normalise the representation to always have an inclusive start if bounded
        if start is not None and not (inclusivity & CountRange.INCLUDE_START):
            start = start + 1
            inclusivity |= CountRange.INCLUDE_START

        # normalise 'never' cases
        if start is not None and end is not None:
            if start > end or (start == end and inclusivity != CountRange.INCLUSIVE):
                start = 0
                end = 0
                inclusivity = CountRange.EXCLUSIVE

        # Normalise the 'eternity' cases
        if start is None and end is None:
            inclusivity = CountRange.INCLUSIVE

        # set attributes using dict to workaround immutability
        self.__dict__['start'] = start
        self.__dict__['end'] = end
        self.__dict__['inclusivity'] = inclusivity

        # provide attribute type info given that attributes are not set directly
        self.start: int
        self.end: int
        self.inclusivity: int

    @classmethod
    def from_start(cls, start: int, inclusivity: int = INCLUSIVE) -> "CountRange":
        """Construct a range starting at start with no end

        :param start: An integer media unit count
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        return cls(start, None, inclusivity)

    @classmethod
    def from_end(cls, end: int, inclusivity: int = INCLUSIVE) -> "CountRange":
        """Construct a range ending at end with no start

        :param end: An integer media unit count
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        return cls(None, end, inclusivity)

    @classmethod
    def from_start_length(cls, start: int, length: int, inclusivity: int = INCLUSIVE) -> "CountRange":
        """Construct a range starting at start and ending at (start + length)

        :param start: An integer media unit count
        :param length: An integer media unit offset, which must be non-negative
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END

        :raises: ValueError if the length is negative"""
        if length < 0:
            raise ValueError("Length must be non-negative")
        return cls(start, start + length, inclusivity)

    @classmethod
    def eternity(cls) -> "CountRange":
        """Return an unbounded range covering all time"""
        return cls(None, None)

    @classmethod
    def never(cls) -> "CountRange":
        """Return a range covering no time"""
        return cls(0, 0, CountRange.EXCLUSIVE)

    @classmethod
    def from_single_count(cls, count: int) -> "CountRange":
        """Construct a range containing only a single count

        :param count: An integer media unit count"""
        return cls(count, count, CountRange.INCLUSIVE)

    @classmethod
    def from_str(cls, s: str, inclusivity: int = INCLUSIVE) -> "CountRange":
        """Convert a string to a range.

        Valid ranges are:
        [<count>_<count>]
        [<count>_<count>)
        (<count>_<count>]
        (<count>_<count>)
        [<count>]
        <count>_<count>
        <count>
        ()

        where <count> is an integer or an empty string.

        The meaning of these is relatively simple: [ indicates including the start count,
        ( indicates excluding it, ] indicates including the end count, and ) indicates excluding it.
        If brackets are ommitted entirely then this is taken as an inclusive range at both ends.
        Omitting a count indicates that there is no bound on that end (ie. the range goes on forever),
        including only a single count by itself indicates a range containing exactly that one count.
        Finally the string "()" represents the empty range.

        :param s: The string to process
        """
        m = re.match(r'(\[|\()?([^_\)\]]+)?(_([^_\)\]]+)?)?(\]|\))?', s)

        if m is None:
            raise ValueError("Invalid CountRange string")

        inc = CountRange.INCLUSIVE
        if m.group(1) == "(":
            inc &= ~CountRange.INCLUDE_START
        if m.group(5) == ")":
            inc &= ~CountRange.INCLUDE_END

        start_str = m.group(2)
        end_str = m.group(4)

        if start_str is not None:
            start = int(start_str)
        else:
            start = None
        if end_str is not None:
            end = int(end_str)
        else:
            end = None

        if start is None and end is None:
            # Ie. we have no first or second count
            if m.group(3) is not None:
                # ie. we have a '_' character
                return cls.eternity()
            else:
                # We have no '_' character, so the whole range is empty
                return cls.never()
        elif start is not None and end is None and m.group(3) is None:
            return cls.from_single_count(start)
        else:
            return cls(start, end, inc)

    @property
    def length(self) -> Union[int, float]:
        """Return the range length as a media unit count"""
        if self.end is None or self.start is None:
            return float("inf")  # there is no int("inf") in python
        return self.end - self.start

    def bounded_before(self) -> bool:
        """Return true if the start of the range is bounded"""
        return self.start is not None

    def bounded_after(self) -> bool:
        """Return true if the end of the range is bounded"""
        return self.end is not None

    def unbounded(self) -> bool:
        """Return true if neither the start or end of the range is bounded"""
        return self.start is None and self.end is None

    def includes_start(self) -> bool:
        """Return true if the start is inclusive"""
        return (self.inclusivity & CountRange.INCLUDE_START) != 0

    def includes_end(self) -> bool:
        """Return true if the end is inclusive"""
        return (self.inclusivity & CountRange.INCLUDE_END) != 0

    def finite(self) -> bool:
        """Return true if the range is finite"""
        return (self.start is not None and self.end is not None)

    def contains_subrange(self, other: "CountRange") -> bool:
        """Returns true if the range supplied lies entirely inside this range"""
        return ((not self.is_empty()) and
                (other.is_empty() or
                 (self.start is None or (other.start is not None and self.start <= other.start)) and
                 (self.end is None or (other.end is not None and self.end >= other.end)) and
                 (not ((self.start is not None) and
                       (other.start is not None) and
                       (self.start == other.start) and
                       (self.inclusivity & CountRange.INCLUDE_START == 0) and
                       (other.inclusivity & CountRange.INCLUDE_START != 0))) and
                 (not ((self.end is not None) and
                       (other.end is not None) and
                       (self.end == other.end) and
                       (self.inclusivity & CountRange.INCLUDE_END == 0) and
                       (other.inclusivity & CountRange.INCLUDE_END != 0)))))

    def to_str(self, with_inclusivity_markers: bool = True) -> str:
        """Convert to [<count>_<count>] format,
        usually the opening and closing delimiters are set to [ or ] for inclusive and ( or ) for exclusive ranges.
        Unbounded ranges have no marker attached to them.

        :param with_inclusivity_markers: if set to False do not include parentheses/brackecount"""
        if self.is_empty():
            if with_inclusivity_markers:
                return "()"
            else:
                return ""
        elif self.start is not None and self.end is not None and self.start == self.end:
            if with_inclusivity_markers:
                return "[" + str(self.start) + "]"
            else:
                return str(self.start)

        if with_inclusivity_markers:
            brackets = [("(", ")"), ("[", ")"), ("(", "]"), ("[", "]")][self.inclusivity]
        else:
            brackets = ("", "")

        return '_'.join([
            (brackets[0] + str(self.start)) if self.start is not None else '',
            (str(self.end) + brackets[1]) if self.end is not None else ''
            ])

    def intersect_with(self, other: "CountRange") -> "CountRange":
        """Return a range which represents the intersection of this range with another"""
        if self.is_empty() or other.is_empty():
            return CountRange.never()

        start = self.start
        if other.start is not None and (self.start is None or self.start < other.start):
            start = other.start
        end = self.end
        if other.end is not None and (self.end is None or self.end > other.end):
            end = other.end

        inclusivity = CountRange.EXCLUSIVE
        if start is None or (start in self and start in other):
            inclusivity |= CountRange.INCLUDE_START
        if end is None or (end in self and end in other):
            inclusivity |= CountRange.INCLUDE_END

        if start is not None and end is not None and start > end:
            return CountRange.never()

        return CountRange(start, end, inclusivity)

    def starts_inside_range(self, other: "CountRange") -> bool:
        """Returns true if the start of this range is located inside the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                ((self.bounded_before() and self.start in other and
                  (not (other.bounded_after() and self.start == other.end and not self.includes_start()))) or
                 (self.bounded_before() and other.bounded_before() and self.start == other.start and
                  (not (self.includes_start() and not other.includes_start()))) or
                 (not self.bounded_before() and not other.bounded_before())))

    def ends_inside_range(self, other: "CountRange") -> bool:
        """Returns true if the end of this range is located inside the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                ((self.bounded_after() and self.end in other and
                  (not (other.bounded_before() and self.end == other.start and not self.includes_end()))) or
                 (self.bounded_after() and other.bounded_after() and self.end == other.end and
                  (not (self.includes_end() and not other.includes_end()))) or
                 (not self.bounded_after() and not other.bounded_after())))

    def is_earlier_than_range(self, other: "CountRange") -> bool:
        """Returns true if this range ends earlier than the start of the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_before() and
                self.bounded_after() and
                (self.end < other.start or
                 (self.end == other.start and
                  not (self.includes_end() and other.includes_start()))))

    def is_later_than_range(self, other: "CountRange") -> bool:
        """Returns true if this range starts later than the end of the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_after() and
                self.bounded_before() and
                (self.start > other.end or
                 (self.start == other.end and
                  not (self.includes_start() and other.includes_end()))))

    def starts_earlier_than_range(self, other: "CountRange") -> bool:
        """Returns true if this range starts earlier than the start of the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_before() and
                (not self.bounded_before() or
                 (self.start < other.start or
                  (self.start == other.start and
                   self.includes_start() and
                   not other.includes_start()))))

    def starts_later_than_range(self, other: "CountRange") -> bool:
        """Returns true if this range starts later than the start of the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                self.bounded_before() and
                (not other.bounded_before() or
                 (self.start > other.start or
                  (self.start == other.start and
                   (not self.includes_start() and other.includes_start())))))

    def ends_earlier_than_range(self, other: "CountRange") -> bool:
        """Returns true if this range ends earlier than the end of the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                self.bounded_after() and
                (not other.bounded_after() or
                 (self.end < other.end or
                  (self.end == other.end and
                   (not self.includes_end() and other.includes_end())))))

    def ends_later_than_range(self, other: "CountRange") -> bool:
        """Returns true if this range ends later than the end of the other."""
        return (not self.is_empty() and
                not other.is_empty() and
                other.bounded_after() and
                (not self.bounded_after() or
                 (self.end > other.end or
                  (self.end == other.end and
                   self.includes_end() and
                   not other.includes_end()))))

    def overlaps_with_range(self, other: "CountRange") -> bool:
        """Returns true if this range and the other overlap."""
        return (not self.is_earlier_than_range(other) and not self.is_later_than_range(other))

    def is_contiguous_with_range(self, other: "CountRange") -> bool:
        """Returns true if the union of this range and the other would be a valid range"""
        return (self.overlaps_with_range(other) or
                (self.is_earlier_than_range(other) and
                 self.end == other.start and
                 (self.includes_end() or other.includes_start())) or
                (self.is_later_than_range(other) and
                 self.start == other.end and
                 (self.includes_start() or other.includes_end())))

    def union_with_range(self, other: "CountRange") -> "CountRange":
        """Returns the union of this range and the other.
        :raises: ValueError if the ranges are not contiguous."""
        if not self.is_contiguous_with_range(other):
            raise ValueError("CountRanges {} and {} are not contiguous, so cannot take the union.".format(self, other))

        return self.extend_to_encompass_range(other)

    def extend_to_encompass_range(self, other: "CountRange") -> "CountRange":
        """Returns the range that encompasses this and the other range."""
        if self.is_empty():
            return other

        if other.is_empty():
            return self

        inclusivity = CountRange.EXCLUSIVE
        if self.start == other.start:
            start = self.start
            inclusivity |= ((self.inclusivity | other.inclusivity) & CountRange.INCLUDE_START)
        elif self.starts_earlier_than_range(other):
            start = self.start
            inclusivity |= (self.inclusivity & CountRange.INCLUDE_START)
        else:
            start = other.start
            inclusivity |= (other.inclusivity & CountRange.INCLUDE_START)

        if self.end == other.end:
            end = self.end
            inclusivity |= ((self.inclusivity | other.inclusivity) & CountRange.INCLUDE_END)
        elif self.ends_later_than_range(other):
            end = self.end
            inclusivity |= (self.inclusivity & CountRange.INCLUDE_END)
        else:
            end = other.end
            inclusivity |= (other.inclusivity & CountRange.INCLUDE_END)

        return CountRange(start, end, inclusivity)

    def split_at(self, count: int) -> Tuple["CountRange", "CountRange"]:
        """Splits a range at a specified count.

        It is guaranteed that the splitting point will be in the *second* CountRange returned, and not in the first.

        :param count: the count to split at
        :returns: A pair of CountRange objects
        :raises: ValueError if count not in self"""

        if count not in self:
            raise ValueError("Cannot split range {} at {}".format(self, count))

        return (CountRange(self.start, count, (self.inclusivity & CountRange.INCLUDE_START)),
                CountRange(count, self.end, CountRange.INCLUDE_START | (self.inclusivity & CountRange.INCLUDE_END)))

    def range_between(self, other: "CountRange") -> "CountRange":
        """Returns the range between the end of the earlier range and the start of the later one"""
        if self.is_contiguous_with_range(other):
            return CountRange.never()
        elif self.is_earlier_than_range(other):
            inclusivity = CountRange.EXCLUSIVE
            if not self.includes_end():
                inclusivity |= CountRange.INCLUDE_START
            if not other.includes_start():
                inclusivity |= CountRange.INCLUDE_END
            return CountRange(self.end, other.start, inclusivity)
        else:
            inclusivity = CountRange.EXCLUSIVE
            if not self.includes_start():
                inclusivity |= CountRange.INCLUDE_END
            if not other.includes_end():
                inclusivity |= CountRange.INCLUDE_START
            return CountRange(other.end, self.start, inclusivity)

    def is_empty(self) -> bool:
        """Returns true on any empty range."""
        return (self.start is not None and
                self.end is not None and
                self.start == self.end and
                self.inclusivity != CountRange.INCLUSIVE)

    def __setattr__(self, name: str, value: Any) -> None:
        """Raises a ValueError if attempt to set an attribute on the immutable CountRange"""
        raise ValueError("Cannot assign to an immutable CountRange")

    def __contains__(self, count: int) -> bool:
        """Returns true if the count is within this range."""
        return ((self.start is None or count >= self.start) and
                (self.end is None or count <= self.end) and
                (not ((self.start is not None) and
                      (count == self.start) and
                      (self.inclusivity & CountRange.INCLUDE_START == 0))) and
                (not ((self.end is not None) and
                      (count == self.end) and
                      (self.inclusivity & CountRange.INCLUDE_END == 0))))

    def __eq__(self, other: Any) -> bool:
        """Return true if the ranges are equal"""
        return (isinstance(other, CountRange) and
                ((self.is_empty() and other.is_empty()) or
                (((self.start is None and other.start is None) or
                  (self.start == other.start and
                   (self.inclusivity & CountRange.INCLUDE_START) == (other.inclusivity & CountRange.INCLUDE_START))) and
                 ((self.end is None and other.end is None) or
                  (self.end == other.end and
                   (self.inclusivity & CountRange.INCLUDE_END) == (other.inclusivity & CountRange.INCLUDE_END))))))

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return "{}.{}.from_str('{}')".format(type(self).__module__, type(self).__name__, self.to_str())
