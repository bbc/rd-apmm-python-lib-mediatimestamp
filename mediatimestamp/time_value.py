# Copyright 2019 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

from typing import Optional, Union, Any
from fractions import Fraction

from .immutable import (
    TimeOffset,
    Timestamp,
    TimeRange,
    SupportsMediaTimeOffset,
    SupportsMediaTimestamp,
    mediatimeoffset,
    mediatimestamp)


TimeValueRepTypes = Union[Timestamp, TimeOffset, int]
TimeValueConstructTypes = Union[SupportsMediaTimeOffset, SupportsMediaTimestamp, int, "TimeValue"]


def _perform_all_conversions(v: TimeValueConstructTypes) -> Union[TimeValueRepTypes, "TimeValue"]:
    if isinstance(v, (int, TimeOffset, TimeValue)):
        return v
    elif isinstance(v, SupportsMediaTimestamp):
        return mediatimestamp(v)
    elif isinstance(v, SupportsMediaTimeOffset):
        return mediatimeoffset(v)
    else:
        raise TypeError("{!r} is not a valid construction type for a TimeValue".format(v))


class TimeValue(object):
    """Represents a media unit time value on a timeline (e.g. Flow).

    Supports one of the following input value representations:
    * TimeOffset
    * Timestamp
    * int (integer media unit count)
    * TimeValue
    * Anything that implements the __mediatimestamp__ magic method
    * Anything that implements the __mediatimeoffset__ magic method

    An optional rate can be set and is required and checked when there is a
    need to convert between representations.

    TimeOffset and Timestamps are converted internally to ints if a rate is
    provided.

    The time value can be converted to a TimeOffset, Timestamp or int using
    the as_*() methods.
    """

    def __init__(self, value: TimeValueConstructTypes, rate: Optional[Fraction] = None):
        """
        :param value: A TimeValue, TimeOffset, TimeStamp or int.
        :param rate: The media unit rate.
        """
        self_rate: Optional[Fraction]
        self_value: TimeValueRepTypes

        value = _perform_all_conversions(value)

        if isinstance(value, TimeValue):
            if rate and value._rate != rate:
                # A rate conversion is required. Convert to a timeoffset here and the
                # conversion at the end using the new rate
                try:
                    self_value = value.as_timeoffset()
                except ValueError:
                    # the representation is a count and so we assume it is as the given rate
                    self_value = value._value
                self_rate = rate
            else:
                self_value = value._value
                self_rate = value._rate
        elif isinstance(value, (TimeOffset, int)):
            self_value = value
            self_rate = rate
        else:
            raise TypeError("Unsupported value type {!r}".format(value))

        # Convert to an int if the value is a TimeOffset and a rate is
        # provided. This allows for more efficient calculations and no
        # normalisation is required.
        if isinstance(self_value, TimeOffset) and self_rate:
            self_value = self_value.to_count(self_rate.numerator, self_rate.denominator)

        # set attributes using dict to workaround immutability
        self.__dict__['_value'] = self_value
        self.__dict__['_rate'] = self_rate

        # provide attribute type info given that attributes are not set directly
        self._value: TimeValueRepTypes
        self._rate: Optional[Fraction]

    @classmethod
    def from_str(cls, s: str, rate: Optional[Fraction] = None) -> "TimeValue":
        """Parse a time value string

        :param s: The string to convert from.
        :param rate: The default media unit rate.
        """
        parts = s.split("@")
        if len(parts) == 2:
            s_val = parts[0]
            rate = Fraction(parts[1])
        elif len(parts) == 1:
            s_val = s
        else:
            raise ValueError("Multiple '@' in TimeValue string")

        if s_val.isdigit() or (
                len(s_val) > 0 and s_val[0] in ['+', '-'] and s_val[1:].isdigit()):
            return cls(int(s_val), rate=rate)
        else:
            # Assuming that it represents a TimeOffset rather than a Timestamp
            return cls(TimeOffset.from_str(s_val), rate=rate)

    def as_timeoffset(self) -> TimeOffset:
        """Returns a TimeOffset representation."""
        if isinstance(self._value, Timestamp):
            return TimeOffset.from_timeoffset(self._value)
        elif isinstance(self._value, TimeOffset):
            return self._value
        else:
            rate = self._require_rate()
            return TimeOffset.from_count(self._value, rate.numerator, rate.denominator)

    def __mediatimeoffset__(self) -> TimeOffset:
        return self.as_timeoffset()

    def as_timestamp(self) -> Timestamp:
        """Returns a Timestamp representation."""
        if isinstance(self._value, Timestamp):
            return self._value
        elif isinstance(self._value, TimeOffset):
            return Timestamp.from_timeoffset(self._value)
        else:
            rate = self._require_rate()
            return Timestamp.from_count(self._value, rate.numerator, rate.denominator)

    def __mediatimestamp__(self) -> Timestamp:
        return self.as_timestamp()

    def __mediatimerange__(self) -> TimeRange:
        return TimeRange.from_single_timestamp(self.as_timestamp())

    def as_count(self) -> int:
        """Returns an integer media unit count representation."""
        if isinstance(self._value, TimeOffset):
            rate = self._require_rate()
            return self._value.to_count(rate.numerator, rate.denominator)
        else:
            return self._value

    @property
    def rate(self) -> Optional[Fraction]:
        return self._rate

    @property
    def value(self) -> TimeValueRepTypes:
        return self._value

    def compare(self, other: TimeValueConstructTypes) -> int:
        """Compare time values and return an integer to indicate the difference"""
        other = _perform_all_conversions(other)
        other_value = self._match_value_type(other)
        if isinstance(self._value, TimeOffset):
            return self._value.compare(other_value)
        else:
            # The logic here follows the TimeOffset implementation
            this_sign = 1 if self >= 0 else -1
            other_sign = 1 if other >= 0 else -1
            if this_sign != other_sign:
                return this_sign
            elif self < other:
                return -this_sign
            elif self > other:
                return this_sign
            else:
                return 0

    def to_str(self, include_rate: bool = True) -> str:
        """Convert to a string"""
        result = str(self._value)
        if self._rate and include_rate:
            result += "@{}".format(self._rate)
        return result

    def __setattr__(self, name: str, value: Any) -> None:
        """Raises a ValueError if attempt to set an attribute on the immutable TimeValue"""
        raise ValueError("Cannot assign to an immutable TimeValue")

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return "{}.{}.from_str('{}')".format(type(self).__module__, type(self).__name__, self.to_str())

    def __abs__(self) -> "TimeValue":
        """Return the absolute TimeValue"""
        return TimeValue(self._value.__abs__(), self._rate)

    def __eq__(self, other: object) -> bool:
        """"Return true if the TimeValues are equal"""
        if not isinstance(other, (SupportsMediaTimestamp, SupportsMediaTimeOffset, int, TimeValue)):
            return False
        other_value = self._match_value_type(other)
        return self._value.__eq__(other_value)

    def __ne__(self, other: object) -> bool:
        """"Return true if the TimeValues are not equal"""
        if not isinstance(other, (SupportsMediaTimestamp, SupportsMediaTimeOffset, int, TimeValue)):
            return True
        other_value = self._match_value_type(other)
        return self._value.__ne__(other_value)

    def __lt__(self, other: TimeValueConstructTypes) -> bool:
        """"Return true if this TimeValue is less than the other TimeValue"""
        other_value = self._match_value_type(other)
        return self._value.__lt__(other_value)  # type: ignore

    def __le__(self, other: TimeValueConstructTypes) -> bool:
        """"Return true if this TimeValue is less than or equal to the other TimeValue"""
        other_value = self._match_value_type(other)
        return self._value.__le__(other_value)  # type: ignore

    def __gt__(self, other: TimeValueConstructTypes) -> bool:
        """"Return true if this TimeValue is greater than the other TimeValue"""
        other_value = self._match_value_type(other)
        return self._value.__gt__(other_value)  # type: ignore

    def __ge__(self, other: TimeValueConstructTypes) -> bool:
        """"Return true if this TimeValue is greater than or equal to the other TimeValue"""
        other_value = self._match_value_type(other)
        return self._value.__ge__(other_value)  # type: ignore

    def __add__(self, other: TimeValueConstructTypes) -> "TimeValue":
        """"Return a TimeValue that is the sum of this and the other TimeValue"""
        other_value = self._match_value_type(other)
        return TimeValue(self._value.__add__(other_value), self._rate)  # type: ignore

    def __sub__(self, other: TimeValueConstructTypes) -> "TimeValue":
        """"Return a TimeValue that is the difference between this and the other TimeValue"""
        other_value = self._match_value_type(other)
        return TimeValue(self._value.__sub__(other_value), self._rate)  # type: ignore

    def __mul__(self, anint: int) -> "TimeValue":
        """"Return this TimeValue multiplied by an integer"""
        self._check_is_int(anint)
        return TimeValue(self._value.__mul__(anint), self._rate)

    def __rmul__(self, anint: int) -> "TimeValue":
        """"Return this TimeValue multiplied by an integer"""
        self._check_is_int(anint)
        return (self * anint)

    def __div__(self, anint: int) -> "TimeValue":
        """"Return this TimeValue divided by an integer, rounded down to -inf"""
        self._check_is_int(anint)
        return (self // anint)

    def __truediv__(self, anint: int) -> "TimeValue":
        """"Return this TimeValue divided by an integer, rounded down to -inf"""
        self._check_is_int(anint)
        return (self // anint)

    def __floordiv__(self, anint: int) -> "TimeValue":
        """"Return this TimeValue divided by an integer, rounded down to -inf"""
        self._check_is_int(anint)
        return TimeValue(self._value.__floordiv__(anint), self._rate)

    def __hash__(self) -> int:
        return hash(repr(self))

    def _match_value_type(self, other: TimeValueConstructTypes) -> TimeValueRepTypes:
        """Converts the other value type to self's value type.

        A rate conversion is done if `other` is a TimeValue and the rate
        differs from self._rate.

        :param other: A TimeValue, TimeOffset, Timestamp or int.
        """
        other_tv = TimeValue(other, rate=self._rate)
        if isinstance(self._value, Timestamp):
            return other_tv.as_timestamp()
        elif isinstance(self._value, TimeOffset):
            return other_tv.as_timeoffset()
        else:
            return other_tv.as_count()

    def _require_rate(self) -> Fraction:
        """Raise an exception if the self._rate is not set or zero.
        """
        if not self._rate:
            raise ValueError("A non-zero TimeValue rate is required for conversion")

        return self._rate

    def _check_is_int(self, anint: Any) -> None:
        """Raise an exception if the parameter is not an integer.

        :param anint: Parameter to check.
        """
        if not isinstance(anint, int):
            raise TypeError("TimeValue operator parameter {!r} is not an 'int'".format(anint))
