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

from typing import Tuple, Optional, Type, TYPE_CHECKING, Protocol, runtime_checkable, Union
from abc import ABCMeta, abstractmethod
import calendar
import time
import re
from datetime import datetime
from dateutil import tz
from fractions import Fraction

from deprecated import deprecated

from ..constants import MAX_NANOSEC, MAX_SECONDS, UTC_LEAP
from ..exceptions import TsValueError

from ._parse import _parse_seconds_fraction, _parse_iso8601
from ._types import RationalTypes

if TYPE_CHECKING:
    from .timerange import TimeRange  # noqa: F401

__all__ = ["Timestamp", "SupportsMediaTimestamp", "mediatimestamp", "TimestampConstructionType"]


TimestampConstructionType = Union["Timestamp", "SupportsMediaTimestamp", int, float]


if TYPE_CHECKING:
    @runtime_checkable
    class SupportsMediaTimestamp (Protocol):
        def __mediatimestamp__(self) -> "Timestamp":
            ...
else:
    class SupportsMediaTimestamp (metaclass=ABCMeta):
        """This is an abstract base class for any class that can be automagically converted into a Timestamp.

        To implement this simply implement the __mediatimestamp__ magic method. No need to inherit from this
        class explicitly.
        """
        @classmethod
        def __subclasshook__(cls, subclass: Type) -> bool:
            if hasattr(subclass, "__mediatimestamp__"):
                return True
            else:
                return False

        @abstractmethod
        def __mediatimestamp__(self) -> "Timestamp":
            ...


def mediatimestamp(v: TimestampConstructionType) -> "Timestamp":
    """This method can be called on any object which supports the __mediatimestamp__ magic method
    and also on a Timestamp, an int or a float.
    It will always return a Timestamp or raise a ValueError.
    """
    if isinstance(v, Timestamp):
        return v
    elif isinstance(v, int):
        return Timestamp(v)
    elif isinstance(v, float):
        return Timestamp.from_float(v)
    elif hasattr(v, "__mediatimestamp__"):
        return v.__mediatimestamp__()
    else:
        raise ValueError("{!r} cannot be converted to a mediatimestamp.Timestamp".format(v))


class Timestamp(object):
    """A nanosecond precision immutable timestamp.

    Note that the canonical representation of a Timestamp is seconds:nanoseconds, e.g. "4:500000000".
    Timestamp in seconds.fractions format (e.g. "4.5") can be parsed, but should not be used for serialization or
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
        raise TsValueError("Cannot assign to an immutable Timestamp")

    def __mediatimestamp__(self) -> "Timestamp":
        return self

    @deprecated(version="4.0.0",
                reason="This method is deprecated. TimeOffset has been merged into Timestamp.")
    def __mediatimeoffset__(self) -> "Timestamp":
        """Legacy method for getting a TimeOffset"""
        return self

    def __mediatimerange__(self) -> "TimeRange":
        from .timerange import TimeRange  # noqa: F811

        return TimeRange.from_single_timestamp(self)

    @classmethod
    def get_time(cls) -> "Timestamp":
        unix_time = time.time()
        abs_unix_time = abs(unix_time)
        unix_sec = int(abs_unix_time)
        unix_ns = int(abs_unix_time*cls.MAX_NANOSEC) - int(abs_unix_time)*cls.MAX_NANOSEC
        unix_sign = 1 if unix_time >= 0 else -1

        return cls.from_unix(unix_sec, unix_ns, unix_sign=unix_sign)

    @classmethod
    @deprecated(version="4.0.0",
                reason="This method is deprecated. TimeOffset has been merged into Timestamp.")
    def from_timeoffset(cls, toff: TimestampConstructionType) -> "Timestamp":
        """Legacy method that converted a TimeOffset to a Timestamp"""
        toff = mediatimestamp(toff)
        return cls(sec=toff.sec, ns=toff.ns, sign=toff.sign)

    @classmethod
    def get_interval_fraction(cls,
                              rate_num: RationalTypes,
                              rate_den: RationalTypes = 1,
                              factor: int = 1) -> "Timestamp":
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        if factor < 1:
            raise TsValueError("invalid interval factor")

        rate = Fraction(rate_num, rate_den)
        ns = int((cls.MAX_NANOSEC * rate.denominator) // (rate.numerator * factor))
        return cls(ns=ns)

    @classmethod
    def from_millisec(cls, millisec: int) -> "Timestamp":
        ns = millisec * 1000**2
        return cls(ns=ns)

    @classmethod
    def from_microsec(cls, microsec: int) -> "Timestamp":
        ns = microsec * 1000
        return cls(ns=ns)

    @classmethod
    def from_nanosec(cls, nanosec: int) -> "Timestamp":
        return cls(ns=nanosec)

    @classmethod
    def from_sec_frac(cls, toff_str: str) -> "Timestamp":
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
    def from_tai_sec_frac(cls, ts_str: str) -> "Timestamp":
        return cls.from_sec_frac(ts_str)

    @classmethod
    def from_sec_nsec(cls, toff_str: str) -> "Timestamp":
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
    def from_tai_sec_nsec(cls, ts_str: str) -> "Timestamp":
        return cls.from_sec_nsec(ts_str)

    @classmethod
    def from_float(cls, toff_float: float) -> "Timestamp":
        """Parse a float as a Timestamp
        """
        sign = 1
        if toff_float < 0:
            sign = -1
        ns = int(abs(toff_float) * cls.MAX_NANOSEC)
        return cls(ns=ns, sign=sign)

    @classmethod
    def from_datetime(cls, dt: datetime) -> "Timestamp":
        minTs = datetime.fromtimestamp(0, tz.gettz('UTC'))
        utcdt = dt.astimezone(tz.gettz('UTC'))
        seconds = abs(int((utcdt - minTs).total_seconds()))
        nanoseconds = utcdt.microsecond * 1000
        if utcdt < minTs:
            sign = -1
            if nanoseconds > 0:
                # The microseconds was for a positive date-time. In a negative
                # unix time it needs to be flipped.
                nanoseconds = cls.MAX_NANOSEC - nanoseconds
        else:
            sign = 1

        return cls.from_unix(unix_sec=seconds, unix_ns=nanoseconds, unix_sign=sign, is_leap=False)

    @classmethod
    def from_iso8601_utc(cls, iso8601utc: str) -> "Timestamp":
        if not iso8601utc.endswith('Z'):
            raise TsValueError("missing 'Z' at end of ISO 8601 UTC format")
        year, month, day, hour, minute, second, ns = _parse_iso8601(iso8601utc[:-1])
        gmtuple = (year, month, day, hour, minute, second - (second == 60))
        secs_since_epoch = calendar.timegm(gmtuple)
        if secs_since_epoch < 0:
            sign = -1
            secs_since_epoch = abs(secs_since_epoch)
            if ns > 0:
                # The ns parsed from the timestamp was for a positive ISO 8601 date-time. In a negative
                # unix time it needs to be flipped.
                ns = cls.MAX_NANOSEC - ns
                secs_since_epoch -= 1
        else:
            sign = 1

        return cls.from_unix(unix_sec=secs_since_epoch, unix_ns=ns, unix_sign=sign, is_leap=(second == 60))

    @classmethod
    def from_smpte_timelabel(cls, timelabel: str) -> "Timestamp":
        r = re.compile(r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)F(\d+) (\d+)/(\d+) UTC([-\+])(\d+):(\d+) TAI([-\+])(\d+)')
        m = r.match(timelabel)
        if m is None:
            raise TsValueError("invalid SMPTE Time Label string format")
        groups = m.groups()
        leap_sec = int(int(groups[5]) == 60)
        local_tm_sec = calendar.timegm(time.struct_time((int(groups[0]), int(groups[1]), int(groups[2]),
                                                         int(groups[3]), int(groups[4]), int(groups[5]) - leap_sec,
                                                         0, 0, 0)))
        rate_num = int(groups[7])
        rate_den = int(groups[8])
        utc_sign = 1
        if groups[9] == '-':
            utc_sign = -1
        tai_sign = 1
        if groups[12] == '-':
            tai_sign = -1
        tai_seconds = (local_tm_sec +
                       leap_sec -
                       utc_sign*(int(groups[10])*60*60 + int(groups[11])*60) -
                       tai_sign*int(groups[13]))
        count = Timestamp(tai_seconds, 0).to_count(rate_num, rate_den, cls.ROUND_UP)
        count += int(groups[6])
        return cls.from_count(count, rate_num, rate_den)

    @classmethod
    def from_str(cls, ts_str: str,) -> "Timestamp":
        """Parse a string as a TimeStamp

        Accepts:
        * SMPTE timelabel
        * ISO 8601 UTC
        * second:nanosecond
        * second.fraction formats
        * "now" to mean the current time.
        """
        if 'F' in ts_str:
            return cls.from_smpte_timelabel(ts_str)
        elif 'T' in ts_str:
            return cls.from_iso8601_utc(ts_str)
        elif ts_str.strip() == 'now':
            return cls.get_time()
        elif '.' in ts_str:
            return cls.from_sec_frac(ts_str)
        else:
            return cls.from_sec_nsec(ts_str)

    @classmethod
    def from_count(cls, count: int, rate_num: RationalTypes, rate_den: RationalTypes = 1) -> "Timestamp":
        """Returns a new Timestamp derived from a count and a particular rate.

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
    def from_unix(cls, unix_sec: int, unix_ns: int, unix_sign: int = 1, is_leap: bool = False) -> "Timestamp":
        leap_sec = 0
        if unix_sign >= 0:
            for tbl_sec, tbl_tai_sec_minus_1 in UTC_LEAP:
                if unix_sec + is_leap >= tbl_sec:
                    leap_sec = (tbl_tai_sec_minus_1 + 1) - tbl_sec
                    break
        else:
            is_leap = False
        return cls(sec=unix_sec+leap_sec, ns=unix_ns, sign=unix_sign)

    def is_null(self) -> bool:
        return self._value == 0

    def get_leap_seconds(self) -> int:
        """ Get the UTC leaps seconds.
        Returns the number of leap seconds that the timestamp is adjusted by when
        converting to UTC.
        """
        leap_sec = 0
        for unix_sec, tai_sec_minus_1 in UTC_LEAP:
            if self.sec >= tai_sec_minus_1:
                leap_sec = (tai_sec_minus_1 + 1) - unix_sec
                break

        return leap_sec

    def to_millisec(self, rounding: "Timestamp.Rounding" = ROUND_NEAREST) -> int:
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

    def to_microsec(self, rounding: "Timestamp.Rounding" = ROUND_NEAREST) -> int:
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

    def to_tai_sec_nsec(self) -> str:
        return self.to_sec_nsec()

    def to_tai_sec_frac(self, fixed_size: bool = False) -> str:
        return self.to_sec_frac(fixed_size=fixed_size)

    def to_float(self) -> float:
        """ Convert to a floating point number of seconds
        """
        return self._value / Timestamp.MAX_NANOSEC

    def to_datetime(self) -> datetime:
        sec, nsec, sign, leap = self.to_unix()
        microsecond = int(round(nsec/1000))
        if microsecond > 999999:
            sec += 1
            microsecond = 0
        if sign < 0 and microsecond > 0:
            # The microseconds is for a negative unix time. In a positive date-time
            # it needs to be flipped.
            microsecond = 1000000 - microsecond
            sec += 1
        dt = datetime.fromtimestamp(sign * sec, tz.gettz('UTC'))
        dt = dt.replace(microsecond=microsecond)

        return dt

    def to_unix(self) -> Tuple[int, int, int, bool]:
        """ Convert to unix seconds.
        Returns a tuple of (seconds, nanoseconds, is_leap), where `is_leap` is
        `True` when the input time corresponds exactly to a UTC leap second.
        Note that this deliberately returns a tuple, to try and avoid confusion.
        """
        if self._value < 0:
            return (self.sec, self.ns, self.sign, False)
        else:
            leap_sec = 0
            is_leap = False
            for unix_sec, tai_sec_minus_1 in UTC_LEAP:
                if self.sec >= tai_sec_minus_1:
                    leap_sec = (tai_sec_minus_1 + 1) - unix_sec
                    is_leap = self.sec == tai_sec_minus_1
                    break

            return (self.sec - leap_sec, self.ns, self.sign, is_leap)

    def to_unix_float(self) -> float:
        """ Convert to unix seconds since the epoch as a floating point number
        """
        (sec, ns, sign, _) = self.to_unix()
        return sign * (sec + ns / Timestamp.MAX_NANOSEC)

    def to_iso8601_utc(self) -> str:
        """ Get printed representation in ISO8601 format (UTC)
        YYYY-MM-DDThh:mm:ss.s
        where `s` is fractional seconds at nanosecond precision (always 9-chars wide)
        """
        unix_s, unix_ns, unix_sign, is_leap = self.to_unix()
        if unix_sign < 0 and unix_ns > 0:
            # The nanoseconds is for a negative unix time. In a positive ISO 8601 date-time
            # it needs to be flipped.
            unix_ns = Timestamp.MAX_NANOSEC - unix_ns
            unix_s += 1
        utc_bd = time.gmtime(unix_sign * unix_s)
        frac_sec = Timestamp(ns=unix_ns)._get_fractional_seconds(fixed_size=True)
        leap_sec = int(is_leap)

        return '%04d-%02d-%02dT%02d:%02d:%02d.%sZ' % (utc_bd.tm_year,
                                                      utc_bd.tm_mon,
                                                      utc_bd.tm_mday,
                                                      utc_bd.tm_hour,
                                                      utc_bd.tm_min,
                                                      utc_bd.tm_sec + leap_sec,
                                                      frac_sec)

    def to_smpte_timelabel(self,
                           rate_num: RationalTypes,
                           rate_den: RationalTypes = 1,
                           utc_offset: Optional[int] = None) -> str:
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        rate = Fraction(rate_num, rate_den)
        count = self.to_count(rate)
        normalised_ts = Timestamp.from_count(count, rate)
        tai_seconds = normalised_ts.sec
        count_on_or_after_second = Timestamp(tai_seconds, 0).to_count(rate, rounding=self.ROUND_UP)
        count_within_second = count - count_on_or_after_second

        unix_sec, unix_ns, unix_sign, is_leap = normalised_ts.to_unix()
        leap_sec = int(is_leap)

        if utc_offset is None:
            # calculate local time offset
            utc_offset_sec = time.timezone
            lt = time.localtime(unix_sec)
            if lt.tm_isdst > 0:
                utc_offset_sec += 60*60
        else:
            utc_offset_sec = utc_offset
        utc_offset_sec_abs = abs(utc_offset_sec)
        utc_offset_hour = utc_offset_sec_abs // (60*60)
        utc_offset_min = (utc_offset_sec_abs % (60*60)) // 60
        utc_sign_char = '+'
        if utc_offset_sec < 0:
            utc_sign_char = '-'

        utc_bd = time.gmtime(unix_sec + utc_offset_sec)

        tai_offset = unix_sec + leap_sec - tai_seconds
        tai_sign_char = '+'
        if tai_offset < 0:
            tai_sign_char = '-'

        return '%04d-%02d-%02dT%02d:%02d:%02dF%02u %u/%u UTC%c%02u:%02u TAI%c%u' % (
                    utc_bd.tm_year, utc_bd.tm_mon, utc_bd.tm_mday,
                    utc_bd.tm_hour, utc_bd.tm_min, utc_bd.tm_sec + leap_sec,
                    count_within_second,
                    rate.numerator, rate.denominator,
                    utc_sign_char, utc_offset_hour, utc_offset_min,
                    tai_sign_char, abs(tai_offset))

    def to_count(self, rate_num: RationalTypes, rate_den: RationalTypes = 1,
                 rounding: "Timestamp.Rounding" = ROUND_NEAREST) -> int:
        """Returns an integer such that if this Timestamp is equal to an exact number of samples at the given rate
        then this is equal, and otherwise the value is rounded as indicated by the rounding parameter.

        :param rate_num: numerator of rate
        :param rate_den: denominator of rate
        :param rounding: One of Timestamp.ROUND_NEAREST, Timestamp.ROUND_UP, or Timestamp.ROUND_DOWN
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
            round_ns = Timestamp.get_interval_fraction(rate, factor=2).to_nanosec()
        elif use_rounding == self.ROUND_UP:
            round_ns = Timestamp.get_interval_fraction(rate, factor=1).to_nanosec() - 1
        else:
            round_ns = 0

        return int(self.sign * (
                    ((abs(self._value) + round_ns) * rate.numerator) // (
                        self.MAX_NANOSEC * rate.denominator)))

    def to_phase_offset(self, rate_num: RationalTypes, rate_den: RationalTypes = 1) -> "Timestamp":
        """Return the smallest positive Timestamp such that abs(self - returnval) represents an integer number of
        samples at the given rate"""
        return self - self.normalise(rate_num, rate_den, rounding=Timestamp.ROUND_DOWN)

    def normalise(self,
                  rate_num: RationalTypes,
                  rate_den: RationalTypes = 1,
                  rounding: "Timestamp.Rounding" = ROUND_NEAREST) -> "Timestamp":
        """Return the nearest Timestamp to self which represents an integer number of samples at the given rate.

        :param rate_num: Rate numerator
        :param rate_den: Rate denominator
        :param rounding: How to round, if set to Timestamp.ROUND_DOWN (resp. Timestamp.ROUND_UP) this method will only
                         return a Timestamp less than or equal to this one (resp. greater than or equal to).
        """
        return self.from_count(self.to_count(rate_num, rate_den, rounding), rate_num, rate_den)

    def compare(self, other_in: TimestampConstructionType) -> int:
        other = mediatimestamp(other_in)
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

    def __abs__(self) -> "Timestamp":
        return Timestamp(self.sec, self.ns, 1)

    def __hash__(self) -> int:
        return self.to_nanosec()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, (int, float, Timestamp)) and self.compare(other) == 0

    def __ne__(self, other: object) -> bool:
        return not (self == other)

    def __lt__(self, other: TimestampConstructionType) -> bool:
        return self.compare(other) < 0

    def __le__(self, other: TimestampConstructionType) -> bool:
        return self.compare(other) <= 0

    def __gt__(self, other: TimestampConstructionType) -> bool:
        return self.compare(other) > 0

    def __ge__(self, other: TimestampConstructionType) -> bool:
        return self.compare(other) >= 0

    def __add__(self, other_in: TimestampConstructionType) -> "Timestamp":
        other = mediatimestamp(other_in)
        ns = self._value + other._value
        return Timestamp(ns=ns)

    def __sub__(self, other_in: TimestampConstructionType) -> "Timestamp":
        other = mediatimestamp(other_in)
        ns = self._value - other._value
        return Timestamp(ns=ns)

    def __iadd__(self, other_in: TimestampConstructionType) -> "Timestamp":
        other = mediatimestamp(other_in)
        tmp = self + other
        return self.__class__(ns=tmp._value)

    def __isub__(self, other_in: TimestampConstructionType) -> "Timestamp":
        other = mediatimestamp(other_in)
        tmp = self - other
        return self.__class__(ns=tmp._value)

    def __mul__(self, anint: int) -> "Timestamp":
        ns = self._value * anint
        return Timestamp(ns=ns)

    def __rmul__(self, anint: int) -> "Timestamp":
        return (self * anint)

    def __div__(self, anint: int) -> "Timestamp":
        return (self // anint)

    def __truediv__(self, anint: int) -> "Timestamp":
        return (self // anint)

    def __floordiv__(self, anint: int) -> "Timestamp":
        ns = self._value // anint
        return Timestamp(ns=ns)

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
