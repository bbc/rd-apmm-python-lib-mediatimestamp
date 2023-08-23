# Copyright 2019 British Broadcasting Corporation
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

from fractions import Fraction
from typing import Union, Type, TYPE_CHECKING, Protocol, runtime_checkable
from abc import ABCMeta, abstractmethod

from ..constants import MAX_NANOSEC, MAX_SECONDS
from ..exceptions import TsValueError

from ._parse import _parse_seconds_fraction
from ._types import RationalTypes

__all__ = ["TimeOffset", "TimeOffsetConstructionType", "SupportsMediaTimeOffset", "mediatimeoffset"]


TimeOffsetConstructionType = Union["TimeOffset", "SupportsMediaTimeOffset", int, float]


if TYPE_CHECKING:
    @runtime_checkable
    class SupportsMediaTimeOffset (Protocol):
        def __mediatimeoffset__(self) -> "TimeOffset":
            ...
else:
    class SupportsMediaTimeOffset (metaclass=ABCMeta):
        """This is an abstract base class for any class that can be automagically converted into a TimeOffset.

        To implement this simply implement the __mediatimeoffset__ magic method. No need to inherit from this
        class explicitly.
        """
        @classmethod
        def __subclasshook__(cls, subclass: Type) -> bool:
            if hasattr(subclass, "__mediatimeoffset__") or hasattr(subclass, "__mediatimestamp__"):
                return True
            else:
                return False

        @abstractmethod
        def __mediatimeoffset__(self) -> "TimeOffset":
            ...


def mediatimeoffset(v: TimeOffsetConstructionType) -> "TimeOffset":
    """This method can be called on any object which supports the __mediatimeoffset__ magic method
    and also on a TimeOffset, an int or a float. It will always return a TimeOffset or raise a ValueError.
    """
    if isinstance(v, TimeOffset):
        return v
    elif isinstance(v, int):
        return TimeOffset(v)
    elif isinstance(v, float):
        return TimeOffset.from_sec_frac(str(v))
    elif hasattr(v, "__mediatimeoffset__"):
        return v.__mediatimeoffset__()
    elif hasattr(v, "__mediatimestamp__"):
        # Since a Timestamp is a TimeOffset we can fall back to this if available
        return v.__mediatimestamp__()  # type: ignore
    else:
        raise ValueError("{!r} cannot be converted to a mediatimestamp.TimeOffset".format(v))


class TimeOffset(object):
    """A nanosecond precision immutable time difference object.

    Note that the canonical representation of a TimeOffset is seconds:nanoseconds, e.g. "4:500000000".
    TimeOffsets in seconds.fractions format (e.g. "4.5") can be parsed, but should not be used for serialization or
    storage due to difficulty disambiguating them from floats.
    """
    class Rounding (int):
        pass

    ROUND_DOWN = Rounding(0)
    ROUND_NEAREST = Rounding(1)
    ROUND_UP = Rounding(2)

    MAX_NANOSEC = MAX_NANOSEC
    MAX_SECONDS = MAX_SECONDS

    def __init__(self, sec: int = 0, ns: int = 0, sign: int = 1):
        if sign < 0:
            sign = -1
        else:
            sign = 1
        value = sign * int(sec * self.MAX_NANOSEC + ns)

        value_limit = self.MAX_SECONDS * self.MAX_NANOSEC - 1
        value = max(-value_limit, min(value_limit, value))

        self._value: int

        self.__dict__['_value'] = value

    @property
    def sec(self) -> int:
        """Returns the whole number of seconds"""
        return int(abs(self._value) // self.MAX_NANOSEC)

    @property
    def ns(self) -> int:
        """Returns the nanoseconds remainder after subtrating the whole number of seconds"""
        return abs(self._value) - self.sec * self.MAX_NANOSEC

    @property
    def sign(self) -> int:
        """Returns 1 if the timeoffset is positive, -1 if negative"""
        if self._value < 0:
            return -1
        else:
            return 1

    def __setattr__(self, name: str, value: object) -> None:
        raise TsValueError("Cannot assign to an immutable TimeOffset")

    def __mediatimeoffset__(self) -> "TimeOffset":
        return self

    @classmethod
    def from_timeoffset(cls, toff: TimeOffsetConstructionType) -> "TimeOffset":
        toff = mediatimeoffset(toff)
        return cls(sec=toff.sec, ns=toff.ns, sign=toff.sign)

    @classmethod
    def get_interval_fraction(cls,
                              rate_num: RationalTypes,
                              rate_den: RationalTypes = 1,
                              factor: int = 1) -> "TimeOffset":
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        if factor < 1:
            raise TsValueError("invalid interval factor")

        rate = Fraction(rate_num, rate_den)
        ns = int((cls.MAX_NANOSEC * rate.denominator) // (rate.numerator * factor))
        return cls(ns=ns)

    @classmethod
    def from_sec_frac(cls, toff_str: str) -> "TimeOffset":
        sec_frac = toff_str.split(".")
        if len(sec_frac) != 1 and len(sec_frac) != 2:
            raise TsValueError("invalid second.fraction format")
        sec = int(sec_frac[0])
        sign = 1
        if sec_frac[0].startswith("-"):
            sign = -1
            sec = abs(sec)
        ns = 0
        if len(sec_frac) > 1:
            ns = _parse_seconds_fraction(sec_frac[1])
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_sec_nsec(cls, toff_str: str) -> "TimeOffset":
        sec_frac = toff_str.split(":")
        if len(sec_frac) != 1 and len(sec_frac) != 2:
            raise TsValueError("invalid second:nanosecond format")
        sec = int(sec_frac[0])
        sign = 1
        if sec_frac[0].startswith("-"):
            sign = -1
            sec = abs(sec)
        ns = 0
        if len(sec_frac) > 1:
            ns = int(sec_frac[1])
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_str(cls, toff_str: str) -> "TimeOffset":
        """Parse a string as a TimeOffset

        Accepts both second:nanosecond and second.fraction formats.
        """
        if '.' in toff_str:
            return cls.from_sec_frac(toff_str)
        else:
            return cls.from_sec_nsec(toff_str)

    @classmethod
    def from_float(cls, toff_float: float) -> "TimeOffset":
        """Parse a float as a TimeOffset
        """
        sign = 1
        if toff_float < 0:
            sign = -1
        ns = int(abs(toff_float) * cls.MAX_NANOSEC)
        return cls(ns=ns, sign=sign)

    @classmethod
    def from_count(cls, count: int, rate_num: RationalTypes, rate_den: RationalTypes = 1) -> "TimeOffset":
        """Returns a new TimeOffset derived from a count and a particular rate.

        :param count: The sample count
        :param rate_num: The numerator of the rate, in Hz
        :param rate_den: The denominator of the rate in Hz
        """
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        sign = 1
        if count < 0:
            sign = -1
        rate = Fraction(rate_num, rate_den)
        ns = (cls.MAX_NANOSEC * abs(count) * rate.denominator) // rate.numerator
        return cls(ns=ns, sign=sign)

    @classmethod
    def from_millisec(cls, millisec: int) -> "TimeOffset":
        ns = millisec * 1000**2
        return cls(ns=ns)

    @classmethod
    def from_microsec(cls, microsec: int) -> "TimeOffset":
        ns = microsec * 1000
        return cls(ns=ns)

    @classmethod
    def from_nanosec(cls, nanosec: int) -> "TimeOffset":
        return cls(ns=nanosec)

    def is_null(self) -> bool:
        return self._value == 0

    def to_sec_nsec(self) -> str:
        """ Convert to <seconds>:<nanoseconds>
        """
        strSign = ""
        if self.sign < 0:
            strSign = "-"
        return u"{}{}:{}".format(strSign, self.sec, self.ns)

    def to_sec_frac(self, fixed_size: bool = False) -> str:
        """ Convert to <seconds>.<fraction>
        """
        strSign = ""
        if self.sign < 0:
            strSign = "-"
        return u"{}{}.{}".format(
            strSign,
            self.sec,
            self._get_fractional_seconds(fixed_size=fixed_size))

    def to_count(self, rate_num: RationalTypes, rate_den: RationalTypes = 1,
                 rounding: "TimeOffset.Rounding" = ROUND_NEAREST) -> int:
        """Returns an integer such that if this TimeOffset is equal to an exact number of samples at the given rate
        then this is equal, and otherwise the value is rounded as indicated by the rounding parameter.

        :param rate_num: numerator of rate
        :param rate_den: denominator of rate
        :param rounding: One of TimeOffset.ROUND_NEAREST, TimeOffset.ROUND_UP, or TimeOffset.ROUND_DOWN
        """
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")

        rate = Fraction(rate_num, rate_den)
        use_rounding = rounding
        if self.sign < 0:
            if use_rounding == self.ROUND_UP:
                use_rounding = self.ROUND_DOWN
            elif use_rounding == self.ROUND_DOWN:
                use_rounding = self.ROUND_UP
        if use_rounding == self.ROUND_NEAREST:
            round_ns = TimeOffset.get_interval_fraction(rate, factor=2).to_nanosec()
        elif use_rounding == self.ROUND_UP:
            round_ns = TimeOffset.get_interval_fraction(rate, factor=1).to_nanosec() - 1
        else:
            round_ns = 0

        return int(self.sign * (
                    ((abs(self._value) + round_ns) * rate.numerator) // (
                        self.MAX_NANOSEC * rate.denominator)))

    def to_phase_offset(self, rate_num: RationalTypes, rate_den: RationalTypes = 1) -> "TimeOffset":
        """Return the smallest positive TimeOffset such that abs(self - returnval) represents an integer number of
        samples at the given rate"""
        return self - self.normalise(rate_num, rate_den, rounding=TimeOffset.ROUND_DOWN)

    def to_millisec(self, rounding: "TimeOffset.Rounding" = ROUND_NEAREST) -> int:
        use_rounding = rounding
        if self.sign < 0:
            if use_rounding == self.ROUND_UP:
                use_rounding = self.ROUND_DOWN
            elif use_rounding == self.ROUND_DOWN:
                use_rounding = self.ROUND_UP
        round_ns = 0
        if use_rounding == self.ROUND_NEAREST:
            round_ns = 1000**2 // 2
        elif use_rounding == self.ROUND_UP:
            round_ns = 1000**2 - 1
        return int(self.sign * ((abs(self._value) + round_ns) // 1000**2))

    def to_microsec(self, rounding: "TimeOffset.Rounding" = ROUND_NEAREST) -> int:
        use_rounding = rounding
        if self.sign < 0:
            if use_rounding == self.ROUND_UP:
                use_rounding = self.ROUND_DOWN
            elif use_rounding == self.ROUND_DOWN:
                use_rounding = self.ROUND_UP
        round_ns = 0
        if use_rounding == self.ROUND_NEAREST:
            round_ns = 1000 // 2
        elif use_rounding == self.ROUND_UP:
            round_ns = 1000 - 1
        return int(self.sign * ((abs(self._value) + round_ns) // 1000))

    def to_nanosec(self) -> int:
        return self._value

    def normalise(self,
                  rate_num: RationalTypes,
                  rate_den: RationalTypes = 1,
                  rounding: "TimeOffset.Rounding" = ROUND_NEAREST) -> "TimeOffset":
        """Return the nearest TimeOffset to self which represents an integer number of samples at the given rate.

        :param rate_num: Rate numerator
        :param rate_den: Rate denominator
        :param rounding: How to round, if set to TimeOffset.ROUND_DOWN (resp. TimeOffset.ROUND_UP) this method will only
                         return a TimeOffset less than or equal to this one (resp. greater than or equal to).
        """
        return self.from_count(self.to_count(rate_num, rate_den, rounding), rate_num, rate_den)

    def compare(self, other_in: TimeOffsetConstructionType) -> int:
        other = mediatimeoffset(other_in)
        if self._value > other._value:
            return 1
        elif self._value < other._value:
            return -1
        else:
            return 0

    def __str__(self) -> str:
        return self.to_sec_nsec()

    def __repr__(self) -> str:
        return "{}.from_sec_nsec({!r})".format("mediatimestamp.immutable." + type(self).__name__, self.to_sec_nsec())

    def __abs__(self) -> "TimeOffset":
        return TimeOffset(self.sec, self.ns, 1)

    def __hash__(self) -> int:
        return self.to_nanosec()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, (int, float, TimeOffset)) and self.compare(other) == 0

    def __ne__(self, other: object) -> bool:
        return not (self == other)

    def __lt__(self, other: TimeOffsetConstructionType) -> bool:
        return self.compare(other) < 0

    def __le__(self, other: TimeOffsetConstructionType) -> bool:
        return self.compare(other) <= 0

    def __gt__(self, other: TimeOffsetConstructionType) -> bool:
        return self.compare(other) > 0

    def __ge__(self, other: TimeOffsetConstructionType) -> bool:
        return self.compare(other) >= 0

    def __add__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        from .timestamp import Timestamp

        other = mediatimeoffset(other_in)
        ns = self._value + other._value

        if not isinstance(self, Timestamp) and not isinstance(other, Timestamp):
            return TimeOffset(ns=ns)
        else:
            return Timestamp(ns=ns)

    def __sub__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        from .timestamp import Timestamp

        other = mediatimeoffset(other_in)
        ns = self._value - other._value

        if isinstance(self, Timestamp) and not isinstance(other, Timestamp):
            return Timestamp(ns=ns)
        else:
            return TimeOffset(ns=ns)

    def __iadd__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        other = mediatimeoffset(other_in)
        tmp = self + other
        return self.__class__(ns=tmp._value)

    def __isub__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        other = mediatimeoffset(other_in)
        tmp = self - other
        return self.__class__(ns=tmp._value)

    def __mul__(self, anint: int) -> "TimeOffset":
        ns = self._value * anint
        return TimeOffset(ns=ns)

    def __rmul__(self, anint: int) -> "TimeOffset":
        return (self * anint)

    def __div__(self, anint: int) -> "TimeOffset":
        return (self // anint)

    def __truediv__(self, anint: int) -> "TimeOffset":
        return (self // anint)

    def __floordiv__(self, anint: int) -> "TimeOffset":
        ns = self._value // anint
        return TimeOffset(ns=ns)

    def _get_fractional_seconds(self, fixed_size: bool = False) -> str:
        div = self.MAX_NANOSEC // 10
        rem = self.ns
        sec_frac = ""

        for i in range(0, 9):
            if not fixed_size and i > 0 and rem == 0:
                break

            sec_frac += '%i' % (rem / div)
            rem %= div
            div //= 10

        return sec_frac
