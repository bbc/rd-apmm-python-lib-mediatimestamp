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
from typing import Tuple, Union, Type, TYPE_CHECKING
from typing_extensions import Protocol, runtime_checkable
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
        (sec, ns, sign) = self._make_valid(int(sec), int(ns), int(sign))

        self.sec: int
        self.ns: int
        self.sign: int

        self.__dict__['sec'] = int(sec)
        self.__dict__['ns'] = int(ns)
        self.__dict__['sign'] = int(sign)

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
        sec = rate.denominator // (rate.numerator * factor)
        rem = rate.denominator % (rate.numerator * factor)
        ns = cls.MAX_NANOSEC * rem // (rate.numerator * factor)
        return cls(sec=sec, ns=ns)

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
    def from_count(cls, count: int, rate_num: RationalTypes, rate_den: RationalTypes = 1) -> "TimeOffset":
        """Returns a new TimeOffset derived from a count and a particular rate.

        :param count: The sample count
        :param rate_num: The numerator of the rate, in Hz
        :param rate_den: The denominator of the rate in Hz
        """
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        rate = Fraction(rate_num, rate_den)
        abs_count = abs(count)
        sec = (abs_count * rate.denominator) // rate.numerator
        rem = (abs_count * rate.denominator) % rate.numerator
        ns = (rem * cls.MAX_NANOSEC) // rate.numerator
        sign = 1
        if count < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_millisec(cls, millisec: int) -> "TimeOffset":
        abs_millisec = abs(millisec)
        sec = abs_millisec // 1000
        ns = (abs_millisec % 1000) * 1000000
        sign = 1
        if millisec < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_microsec(cls, microsec: int) -> "TimeOffset":
        abs_microsec = abs(microsec)
        sec = abs_microsec // 1000000
        ns = (abs_microsec % 1000000) * 1000
        sign = 1
        if microsec < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_nanosec(cls, nanosec: int) -> "TimeOffset":
        abs_nanosec = abs(nanosec)
        sec = abs_nanosec // cls.MAX_NANOSEC
        ns = abs_nanosec % cls.MAX_NANOSEC
        sign = 1
        if nanosec < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    def is_null(self) -> bool:
        return self.sec == 0 and self.ns == 0

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
        abs_off = self.__abs__()
        use_rounding = rounding
        if self.sign < 0:
            if use_rounding == self.ROUND_UP:
                use_rounding = self.ROUND_DOWN
            elif use_rounding == self.ROUND_DOWN:
                use_rounding = self.ROUND_UP
        if use_rounding == self.ROUND_NEAREST:
            rnd_off = TimeOffset.get_interval_fraction(rate, factor=2)
        elif use_rounding == self.ROUND_UP:
            rnd_off = TimeOffset.get_interval_fraction(rate, factor=1) - TimeOffset(0, 1)
        else:
            rnd_off = TimeOffset()
        if rnd_off.sign > 0:
            abs_off += rnd_off

        # off_at_rate = (off_sec + off_nsec) / (rate_den / rate_num)
        #             = (off_sec x rate_num / rate_den) + (off_nsec x rate_num) / rate_den)
        #             = {f1} + {f2}
        # reduce {f1} as follows: a*b/c = ((a/c)*c + a%c) * b) / c = (a/c)*b + (a%c)*b/c
        # then combine the f1 and f2 nanosecond values before division by rate_den to avoid loss of precision when
        # off_sec and off_nsec are not multiples of rate_den, but (off_sec + off_nsec) is
        f1_whole = (abs_off.sec // rate.denominator) * rate.numerator
        f1_dennsec = (abs_off.sec % rate.denominator) * rate.numerator * self.MAX_NANOSEC
        f2_dennsec = abs_off.ns * rate.numerator
        return self.sign * (f1_whole + (f1_dennsec + f2_dennsec) // (rate.denominator * self.MAX_NANOSEC))

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
            round_ns = 1000000 // 2
        elif use_rounding == self.ROUND_UP:
            round_ns = 1000000 - 1
        return self.sign * (self.sec*1000 + (self.ns + round_ns)//1000000)

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
        return self.sign * (self.sec*1000000 + (self.ns + round_ns)//1000)

    def to_nanosec(self) -> int:
        return self.sign * (self.sec*self.MAX_NANOSEC + self.ns)

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
        if self.sign != other.sign:
            return self.sign
        elif self.sec < other.sec:
            return -self.sign
        elif self.sec > other.sec:
            return self.sign
        elif self.ns < other.ns:
            return -self.sign
        elif self.ns > other.ns:
            return self.sign
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
        sec = self.sign*self.sec + other.sign*other.sec
        ns = self.sign*self.ns + other.sign*other.ns

        if not isinstance(self, Timestamp) and not isinstance(other, Timestamp):
            return TimeOffset(sec, ns)
        else:
            return Timestamp(sec, ns)

    def __sub__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        from .timestamp import Timestamp

        other = mediatimeoffset(other_in)
        sec = self.sign*self.sec - other.sign*other.sec
        ns = self.sign*self.ns - other.sign*other.ns

        if isinstance(self, Timestamp) and not isinstance(other, Timestamp):
            return Timestamp(sec, ns)
        else:
            return TimeOffset(sec, ns)

    def __iadd__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        other = mediatimeoffset(other_in)
        tmp = self + other
        return self.__class__(tmp.sec, tmp.ns, tmp.sign)

    def __isub__(self, other_in: TimeOffsetConstructionType) -> "TimeOffset":
        other = mediatimeoffset(other_in)
        tmp = self - other
        return self.__class__(tmp.sec, tmp.ns, tmp.sign)

    def __mul__(self, anint: int) -> "TimeOffset":
        sec = self.sec * abs(anint)
        ns = self.ns * abs(anint)

        if anint < 0:
            sign = self.sign * -1
        else:
            sign = self.sign

        if ns >= self.MAX_NANOSEC:
            sec += (ns // self.MAX_NANOSEC)
            ns %= self.MAX_NANOSEC

        return TimeOffset(sec, ns, sign)

    def __rmul__(self, anint: int) -> "TimeOffset":
        return (self * anint)

    def __div__(self, anint: int) -> "TimeOffset":
        return (self // anint)

    def __truediv__(self, anint: int) -> "TimeOffset":
        return (self // anint)

    def __floordiv__(self, anint: int) -> "TimeOffset":
        (sec, ns, sign) = (self.sec, self.ns, self.sign)
        abs_anint = abs(anint)
        sec = sec // abs_anint
        ns = int((self.ns + (self.sec % abs_anint) * self.MAX_NANOSEC) / abs_anint + 5e-10)

        sec = sec + ns // self.MAX_NANOSEC
        ns = ns % self.MAX_NANOSEC
        if anint < 0:
            sign *= -1
        return TimeOffset(sec, ns, sign)

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

    def _make_valid(self, sec: int, ns: int, sign: int) -> Tuple[int, int, int]:
        if sign > 0 or (sec == 0 and ns == 0):
            sign = 1
        else:
            sign = -1

        sec += (ns // self.MAX_NANOSEC)
        ns %= self.MAX_NANOSEC

        if sec < 0 or (sec == 0 and ns < 0):
            sec *= -1
            ns *= -1
            sign *= -1

        if ns < 0:
            sec -= 1
            ns += self.MAX_NANOSEC

        if sec >= self.MAX_SECONDS:
            sec = self.MAX_SECONDS - 1
            ns = self.MAX_NANOSEC - 1

        return (sec, ns, sign)
