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

"""This library provides a class TimeOffset which stores an mutable signed time difference value with nanosecond
precision.

It also provides a class Timestamp which is a descendent of TimeOffset which represents a mutable positive time offset
since the epoch (ie. 1970-01-01T00:00:00.000000000Z)

And finally it includes a mutable TimeRange object which stores a range between two Timestamps.

These data types are of use in a number of situations, but particularly for code that will handle PTP timestamps, which
are normally stored in this fashion.
"""

from __future__ import print_function
from __future__ import absolute_import

from six import integer_types

from .bases import BaseTimeOffset, BaseTimeRange

import calendar
import time
import re
from datetime import datetime
from dateutil import tz
try:
    import pyipputils.ipptimestamp
    IPP_UTILS = True
except ImportError:
    IPP_UTILS = False

from .constants import MAX_NANOSEC, MAX_SECONDS, UTC_LEAP
from .exceptions import TsValueError

__all__ = ["TimeOffset", "Timestamp", "TimeRange"]


def _parse_seconds_fraction(frac):
    """ Parse the fraction part of a timestamp seconds, using maximum 9 digits
    Returns the nanoseconds
    """
    ns = 0
    mult = TimeOffset.MAX_NANOSEC
    for c in frac:
        if c < '0' or c > '9' or int(mult) < 1:
            break
        mult = mult / 10
        ns += mult * int(c)
    return ns


def _parse_iso8601(iso8601):
    """ Limited ISO 8601 timestamp parse; expands YYYY-MM-DDThh:mm:ss.s
    Returns tuple of (year, month, day, hours, mins, seconds, nanoseconds)
    """
    iso_date_time = iso8601.split("T")
    if len(iso_date_time) != 2:
        raise TsValueError("invalid or unsupported ISO 8601 UTC format")
    iso_date = iso_date_time[0].split("-")
    iso_time = iso_date_time[1].split(":")
    if len(iso_date) != 3 or len(iso_time) != 3:
        raise TsValueError("invalid or unsupported ISO 8601 UTC format")
    sec_frac = iso_time[2].split(".")
    if len(sec_frac) != 1 and len(sec_frac) != 2:
        raise TsValueError("invalid or unsupported ISO 8601 UTC format")
    sec = sec_frac[0]
    ns = 0
    if len(sec_frac) > 1:
        ns = _parse_seconds_fraction(sec_frac[1])
    return (int(iso_date[0]), int(iso_date[1]), int(iso_date[2]), int(iso_time[0]), int(iso_time[1]), int(sec), ns)


class TimeOffset(BaseTimeOffset):
    """A nanosecond precision mutable time difference object.

    Note that the canonical representation of a TimeOffset is seconds:nanoseconds, e.g. "4:500000000".
    TimeOffsets in seconds.fractions format (e.g. "4.5") can be parsed, but should not be used for serialization or
    storage due to difficulty disambiguating them from floats.
    """
    ROUND_DOWN = 0
    ROUND_NEAREST = 1
    ROUND_UP = 2

    MAX_NANOSEC = MAX_NANOSEC
    MAX_SECONDS = MAX_SECONDS

    def __init__(self, sec=0, ns=0, sign=1):
        super(TimeOffset, self).__init__(sec, ns, sign)
        self._make_valid()

    @classmethod
    def from_timeoffset(cls, toff):
        return cls(sec=toff.sec, ns=toff.ns, sign=toff.sign)

    @classmethod
    def get_interval_fraction(cls, rate_num, rate_den=1, factor=1):
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        if factor < 1:
            raise TsValueError("invalid interval factor")
        sec = rate_den // (rate_num * factor)
        rem = rate_den % (rate_num * factor)
        ns = cls.MAX_NANOSEC * rem // (rate_num * factor)
        return cls(sec=sec, ns=ns)

    @classmethod
    def from_sec_frac(cls, toff_str):
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
    def from_sec_nsec(cls, toff_str):
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
    def from_str(cls, toff_str):
        """Parse a string as a TimeOffset

        Accepts both second:nanosecond and second.fraction formats.
        """
        if '.' in toff_str:
            return cls.from_sec_frac(toff_str)
        else:
            return cls.from_sec_nsec(toff_str)

    @classmethod
    def from_count(cls, count, rate_num, rate_den=1):
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        abs_count = abs(count)
        sec = (abs_count * rate_den) // rate_num
        rem = (abs_count * rate_den) % rate_num
        ns = (rem * cls.MAX_NANOSEC) // rate_num
        sign = 1
        if count < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_millisec(cls, millisec):
        abs_millisec = abs(millisec)
        sec = abs_millisec // 1000
        ns = (abs_millisec % 1000) * 1000000
        sign = 1
        if millisec < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_microsec(cls, microsec):
        abs_microsec = abs(microsec)
        sec = abs_microsec // 1000000
        ns = (abs_microsec % 1000000) * 1000
        sign = 1
        if microsec < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    @classmethod
    def from_nanosec(cls, nanosec):
        abs_nanosec = abs(nanosec)
        sec = abs_nanosec // cls.MAX_NANOSEC
        ns = abs_nanosec % cls.MAX_NANOSEC
        sign = 1
        if nanosec < 0:
            sign = -1
        return cls(sec=sec, ns=ns, sign=sign)

    def is_null(self):
        return self.sec == 0 and self.ns == 0

    def set_value(self, sec=0, ns=0, sign=1):
        self.sec = sec
        self.ns = ns
        self.sign = sign
        self._make_valid()

    def to_sec_nsec(self):
        """ Convert to <seconds>:<nanoseconds>
        """
        strSign = ""
        if self.sign < 0:
            strSign = "-"
        return u"{}{}:{}".format(strSign, self.sec, self.ns)

    def to_sec_frac(self, fixed_size=False):
        """ Convert to <seconds>.<fraction>
        """
        strSign = ""
        if self.sign < 0:
            strSign = "-"
        return u"{}{}.{}".format(
            strSign,
            self.sec,
            self._get_fractional_seconds(fixed_size=fixed_size))

    def to_count(self, rate_num, rate_den=1, rounding=ROUND_NEAREST):
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        abs_off = self.__abs__()
        use_rounding = rounding
        if self.sign < 0:
            if use_rounding == self.ROUND_UP:
                use_rounding = self.ROUND_DOWN
            elif use_rounding == self.ROUND_DOWN:
                use_rounding = self.ROUND_UP
        if use_rounding == self.ROUND_NEAREST:
            rnd_off = TimeOffset.get_interval_fraction(rate_num, rate_den, 2)
        elif use_rounding == self.ROUND_UP:
            rnd_off = TimeOffset.get_interval_fraction(rate_num, rate_den, 1) - TimeOffset(0, 1)
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
        f1_whole = (abs_off.sec // rate_den) * rate_num
        f1_dennsec = (abs_off.sec % rate_den) * rate_num * self.MAX_NANOSEC
        f2_dennsec = abs_off.ns * rate_num
        return self.sign * (f1_whole + (f1_dennsec + f2_dennsec) // (rate_den * self.MAX_NANOSEC))

    def to_millisec(self, rounding=ROUND_NEAREST):
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

    def to_microsec(self, rounding=ROUND_NEAREST):
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

    def to_nanosec(self):
        return self.sign * (self.sec*self.MAX_NANOSEC + self.ns)

    def normalise(self, rate_num, rate_den=1, rounding=ROUND_NEAREST):
        return self.from_count(self.to_count(rate_num, rate_den, rounding), rate_num, rate_den)

    def compare(self, other_in):
        other = self._cast_arg(other_in)
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

    def __repr__(self):
        return self.to_sec_nsec()

    def __abs__(self):
        return TimeOffset(self.sec, self.ns, 1)

    def __hash__(self):
        return self.to_nanosec()

    def __eq__(self, other):
        return isinstance(self._cast_arg(other), BaseTimeOffset) and self.compare(other) == 0

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.compare(other) < 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __add__(self, other_in):
        other = self._cast_arg(other_in)
        toff = TimeOffset(self.sec, self.ns, self.sign)
        toff += other
        return self.__class__(toff.sec, toff.ns, toff.sign)

    def __sub__(self, other_in):
        other = self._cast_arg(other_in)
        toff = TimeOffset(self.sec, self.ns, self.sign)
        toff -= other
        if isinstance(other, Timestamp) and isinstance(self, Timestamp):
            return toff
        else:
            return self.__class__(toff.sec, toff.ns, toff.sign)

    def __iadd__(self, other_in):
        other = self._cast_arg(other_in)
        sec = self.sign*self.sec + other.sign*other.sec
        ns = self.sign*self.ns + other.sign*other.ns
        self._complete_iadd_or_isub(sec, ns)
        return self

    def __isub__(self, other_in):
        other = self._cast_arg(other_in)
        sec = self.sign*self.sec - other.sign*other.sec
        ns = self.sign*self.ns - other.sign*other.ns
        self._complete_iadd_or_isub(sec, ns)
        return self

    def __mul__(self, anint):
        toff = TimeOffset(self.sec, self.ns, self.sign)
        toff *= anint
        return self.__class__(toff.sec, toff.ns, toff.sign)

    def __rmul__(self, anint):
        toff = TimeOffset(self.sec, self.ns, self.sign)
        toff *= anint
        return self.__class__(toff.sec, toff.ns, toff.sign)

    def __truediv__(self, anint):
        toff = type(self)(self.sec, self.ns, self.sign)
        abs_anint = abs(anint)
        sec = self.sec // abs_anint
        ns = int((self.ns + (self.sec % abs_anint) * self.MAX_NANOSEC) / abs_anint + 5e-10)

        toff.sec = sec + ns // self.MAX_NANOSEC
        toff.ns = ns % self.MAX_NANOSEC
        if anint < 0:
            toff.sign *= -1
        toff._make_valid()
        return toff

    def __floordiv__(self, anint):
        return self.__truediv__(anint)

    def __imul__(self, anint):
        abs_anint = abs(anint)
        ns_sec = self.ns * (abs_anint // self.MAX_NANOSEC)
        ns = self.ns * (abs_anint % self.MAX_NANOSEC)

        self.sec = self.sec * abs_anint + ns_sec + ns // self.MAX_NANOSEC
        self.ns = ns % self.MAX_NANOSEC
        if anint < 0:
            self.sign *= -1
        self._make_valid()
        return self

    def _complete_iadd_or_isub(self, sec, ns):
        if ns >= self.MAX_NANOSEC:
            ns -= self.MAX_NANOSEC
            sec += 1
        elif -ns >= self.MAX_NANOSEC:
            ns += self.MAX_NANOSEC
            sec -= 1
        if sec < 0 and ns > 0:
            ns -= self.MAX_NANOSEC
            sec += 1
        elif sec > 0 and ns < 0:
            ns += self.MAX_NANOSEC
            sec -= 1

        if sec < 0 or ns < 0:
            self.sign = -1
            self.sec = abs(sec)
            self.ns = abs(ns)
        else:
            self.sign = 1
            self.sec = sec
            self.ns = ns
        self._make_valid()

    def _get_fractional_seconds(self, fixed_size=False):
        div = self.MAX_NANOSEC / 10
        rem = self.ns
        sec_frac = ""

        for i in range(0, 9):
            if not fixed_size and i > 0 and rem == 0:
                break

            sec_frac += '%i' % (rem / div)
            rem %= div
            div /= 10

        return sec_frac

    def _cast_arg(self, other):
        if isinstance(other, integer_types):
            return TimeOffset(other)
        elif isinstance(other, float):
            return TimeOffset.from_sec_frac(str(other))
        elif isinstance(other, BaseTimeOffset) and not isinstance(other, TimeOffset):
            return TimeOffset.from_timeoffset(other)
        else:
            return other

    def _make_valid(self):
        if self.sign >= 0 or (self.sec == 0 and self.ns == 0):
            self.sign = 1
        else:
            self.sign = -1
        if self.sec < 0:
            self.sec = 0
            self.ns = 0
            self.sign = 1
        elif self.ns < 0:
            self.ns = 0
        elif self.ns >= self.MAX_NANOSEC:
            self.ns = self.MAX_NANOSEC - 1


class Timestamp(TimeOffset):
    """A nanosecond precision mutable timestamp."""
    def __init__(self, sec=0, ns=0, sign=1):
        super(Timestamp, self).__init__(sec, ns, sign)

    @classmethod
    def get_time(cls, force_pure_python=False):
        if not force_pure_python and IPP_UTILS:
            (sign, sec, ns) = pyipputils.ipptimestamp.ipp_ts_gettime()
            return cls(sign=sign, sec=sec, ns=ns)
        else:
            # Fall back to system time if IPP Utils not found
            # No PTP so not as accurate
            utc_time = time.time()
            return cls.from_utc(int(utc_time), int(utc_time*cls.MAX_NANOSEC) - int(utc_time)*cls.MAX_NANOSEC)

    @classmethod
    def from_tai_sec_frac(cls, ts_str):
        return cls.from_sec_frac(ts_str)

    @classmethod
    def from_tai_sec_nsec(cls, ts_str):
        return cls.from_sec_nsec(ts_str)

    @classmethod
    def from_datetime(cls, dt):
        minTs = datetime.fromtimestamp(0, tz.gettz('UTC'))
        utcdt = dt.astimezone(tz.gettz('UTC'))
        seconds = int((utcdt - minTs).total_seconds())
        nanoseconds = utcdt.microsecond * 1000

        return cls.from_utc(seconds, nanoseconds, False)

    @classmethod
    def from_iso8601_utc(cls, iso8601utc):
        if not iso8601utc.endswith('Z'):
            raise TsValueError("missing 'Z' at end of ISO 8601 UTC format")
        year, month, day, hour, minute, second, ns = _parse_iso8601(iso8601utc[:-1])
        gmtuple = (year, month, day, hour, minute, second - (second == 60))
        secs_since_epoch = calendar.timegm(gmtuple)
        return cls.from_utc(secs_since_epoch, ns, (second == 60))

    @classmethod
    def from_smpte_timelabel(cls, timelabel):
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
    def from_str(cls, ts_str, force_pure_python=False):
        """Parse a string as a TimeStamp

        Accepts SMPTE timelabel, ISO 8601 UTC, second:nanosecond and second.fraction formats, along with "now" to mean
        the current time.
        """
        if 'F' in ts_str:
            return cls.from_smpte_timelabel(ts_str)
        elif 'T' in ts_str:
            return cls.from_iso8601_utc(ts_str)
        elif ts_str.strip() == 'now':
            return cls.get_time(force_pure_python=force_pure_python)
        else:
            return super(Timestamp, cls).from_str(ts_str)

    @classmethod
    def from_utc(cls, utc_sec, utc_ns, is_leap=False):
        leap_sec = 0
        for tbl_sec, tbl_tai_sec_minus_1 in UTC_LEAP:
            if utc_sec >= tbl_sec:
                leap_sec = (tbl_tai_sec_minus_1 + 1) - tbl_sec
                break
        return cls(sec=utc_sec+leap_sec+is_leap, ns=utc_ns)

    def get_leap_seconds(self):
        """ Get the UTC leaps seconds.
        Returns the number of leap seconds that the timestamp is adjusted by when
        converting to UTC.
        """
        leap_sec = 0
        for utc_sec, tai_sec_minus_1 in UTC_LEAP:
            if self.sec >= tai_sec_minus_1:
                leap_sec = (tai_sec_minus_1 + 1) - utc_sec
                break

        return leap_sec

    def to_tai_sec_nsec(self):
        return self.to_sec_nsec()

    def to_tai_sec_frac(self, fixed_size=False):
        return self.to_sec_frac(fixed_size=fixed_size)

    def to_datetime(self):
        sec, nsec, leap = self.to_utc()
        dt = datetime.fromtimestamp(sec, tz.gettz('UTC'))
        dt = dt.replace(microsecond=int(round(nsec/1000)))

        return dt

    def to_utc(self):
        """ Convert to UTC.
        Returns a tuple of (seconds, nanoseconds, is_leap), where `is_leap` is
        `True` when the input time corresponds exactly to a UTC leap second.
        Note that this deliberately returns a tuple, to try and avoid confusion.
        """
        leap_sec = 0
        is_leap = False
        for utc_sec, tai_sec_minus_1 in UTC_LEAP:
            if self.sec >= tai_sec_minus_1:
                leap_sec = (tai_sec_minus_1 + 1) - utc_sec
                is_leap = self.sec == tai_sec_minus_1
                break

        return (self.sec - leap_sec, self.ns, is_leap)

    def to_iso8601_utc(self):
        """ Get printed representation in ISO8601 format (UTC)
        YYYY-MM-DDThh:mm:ss.s
        where `s` is fractional seconds at nanosecond precision (always 9-chars wide)
        """
        utc_s, utc_ns, is_leap = self.to_utc()
        utc_bd = time.gmtime(utc_s)
        frac_sec = self._get_fractional_seconds(fixed_size=True)
        leap_sec = int(is_leap)
        return '%04d-%02d-%02dT%02d:%02d:%02d.%sZ' % (utc_bd.tm_year,
                                                      utc_bd.tm_mon,
                                                      utc_bd.tm_mday,
                                                      utc_bd.tm_hour,
                                                      utc_bd.tm_min,
                                                      utc_bd.tm_sec + leap_sec,
                                                      frac_sec)

    def to_smpte_timelabel(self, rate_num, rate_den=1, utc_offset=None):
        if rate_num <= 0 or rate_den <= 0:
            raise TsValueError("invalid rate")
        count = self.to_count(rate_num, rate_den)
        normalised_ts = Timestamp.from_count(count, rate_num, rate_den)
        tai_seconds = normalised_ts.sec
        count_on_or_after_second = Timestamp(tai_seconds, 0).to_count(rate_num, rate_den, self.ROUND_UP)
        count_within_second = count - count_on_or_after_second

        utc_sec, utc_ns, is_leap = normalised_ts.to_utc()
        leap_sec = int(is_leap)

        if utc_offset is None:
            # calculate local time offset
            utc_offset_sec = time.timezone
            lt = time.localtime(utc_sec)
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

        utc_bd = time.gmtime(utc_sec + utc_offset_sec)

        tai_offset = utc_sec + leap_sec - tai_seconds
        tai_sign_char = '+'
        if tai_offset < 0:
            tai_sign_char = '-'

        return '%04d-%02d-%02dT%02d:%02d:%02dF%02u %u/%u UTC%c%02u:%02u TAI%c%u' % (
                    utc_bd.tm_year, utc_bd.tm_mon, utc_bd.tm_mday,
                    utc_bd.tm_hour, utc_bd.tm_min, utc_bd.tm_sec + leap_sec,
                    count_within_second,
                    rate_num, rate_den,
                    utc_sign_char, utc_offset_hour, utc_offset_min,
                    tai_sign_char, abs(tai_offset))

    def _make_valid(self):
        super(Timestamp, self)._make_valid()
        if self.sign < 0:
            self.sec = 0
            self.ns = 0
            self.sign = 1
        elif self.sec >= self.MAX_SECONDS:
            self.sec = self.MAX_SECONDS - 1
            self.ns = self.MAX_NANOSEC - 1


class TimeRange (BaseTimeRange):
    """A nanosecond mutable precision time range object"""

    EXCLUSIVE = 0x0
    INCLUDE_START = 0x1
    INCLUDE_END = 0x2
    INCLUSIVE = 0x3

    def __init__(self, start, end, inclusivity=INCLUSIVE):
        """Construct a time range starting at start and ending at end

        :param start: A Timestamp or None
        :param end: A Timestamp or None
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        super(TimeRange, self).__init__(start, end, inclusivity)

    @classmethod
    def from_timerange(cls, other):
        """Construct a mutable timerange from another timerange (which might be immutable)"""
        return TimeRange(Timestamp.from_timeoffset(other.start),
                         Timestamp.from_timeoffset(other.end),
                         other.inclusivity)

    @classmethod
    def from_start(cls, start, inclusivity=INCLUSIVE):
        """Construct a time range starting at start with no end

        :param start: A Timestamp
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        return cls(start, None, inclusivity)

    @classmethod
    def from_end(cls, end, inclusivity=INCLUSIVE):
        """Construct a time range ending at end with no start

        :param end: A Timestamp
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END"""
        return cls(None, end, inclusivity)

    @classmethod
    def from_start_length(cls, start, length, inclusivity=INCLUSIVE):
        """Construct a time range starting at start and ending at (start + length)

        :param start: A Timestamp
        :param length: A TimeOffset, which must be non-negative
        :param inclusivity: a combination of flags INCLUDE_START and INCLUDE_END

        :raises: TsValueError if the length is negative"""
        if length < TimeOffset():
            raise TsValueError("Length must be non-negative")
        return cls(start, start + length, inclusivity)

    @classmethod
    def eternity(cls):
        """Return an unbounded time range covering all time"""
        return cls(None, None)

    @classmethod
    def never(cls):
        """Return a time range covering no time"""
        return cls(Timestamp(), Timestamp(), TimeRange.EXCLUSIVE)

    @classmethod
    def from_single_timestamp(cls, ts):
        """Construct a time range containing only a single timestamp

        :param ts: A Timestamp"""
        return cls(ts, ts, TimeRange.INCLUSIVE)

    @classmethod
    def from_str(cls, s, inclusivity=INCLUSIVE):
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

        inc = TimeRange.INCLUSIVE
        if m.group(1) == "(":
            inc &= ~TimeRange.INCLUDE_START
        if m.group(5) == ")":
            inc &= ~TimeRange.INCLUDE_END

        start = m.group(2)
        end = m.group(4)

        if start is not None:
            start = Timestamp.from_str(start)
        if end is not None:
            end = Timestamp.from_str(end)

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
    def length(self):
        if self.end is None or self.start is None:
            return float("inf")
        return self.end - self.start

    @length.setter
    def length(self, new_length):
        """Sets the length of the range. If the range already has a start time set then it is left
        unchanged, if it has only an end time then that is left unchanged and a new start time is set,
        and if neither is set then a TsValueError is raised.

        When a length is set on a timerange the inclusivity is changed to exclude the newly added end of the
        range, but otherwise not changed.

        :param new_length: A TimeOffset, which must be positive
        :raises: TsValueError is length is invalid or the original range was eternity()"""
        if new_length < TimeOffset():
            raise TsValueError("length must be positive")

        if self.start is None:
            if self.end is None:
                raise TsValueError("Cannot set length on a time range with no start or end")
            self.start = self.end - new_length
            self.inclusivity &= ~TimeRange.INCLUDE_START
        else:
            self.end = self.start + new_length
            self.inclusivity &= ~TimeRange.INCLUDE_END

    def __contains__(self, ts):
        """Returns true if the timestamp is within this range."""
        return ((self.start is None or ts >= self.start) and
                (self.end is None or ts <= self.end) and
                (not ((self.start is not None) and
                      (ts == self.start) and
                      (self.inclusivity & TimeRange.INCLUDE_START == 0))) and
                (not ((self.end is not None) and
                      (ts == self.end) and
                      (self.inclusivity & TimeRange.INCLUDE_END == 0))))

    def __eq__(self, other):
        return (isinstance(other, TimeRange) and
                ((self.is_empty() and other.is_empty()) or
                (((self.start is None and other.start is None) or
                  (self.start == other.start and
                   (self.inclusivity & TimeRange.INCLUDE_START) == (other.inclusivity & TimeRange.INCLUDE_START))) and
                 ((self.end is None and other.end is None) or
                  (self.end == other.end and
                   (self.inclusivity & TimeRange.INCLUDE_END) == (other.inclusivity & TimeRange.INCLUDE_END))))))

    def __repr__(self):
        return "TimeRange.from_str('{}')".format(self.to_sec_nsec_range())

    def contains_subrange(self, tr):
        """Returns True if the timerange supplied lies entirely inside this timerange"""
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

    def to_sec_nsec_range(self, with_inclusivity_markers=True):
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
            brackets = ["", ""]

        return '_'.join([
            (brackets[0] + self.start.to_tai_sec_nsec()) if self.start is not None else '',
            (self.end.to_tai_sec_nsec() + brackets[1]) if self.end is not None else ''
            ])

    def intersect_with(self, tr):
        """Return a range which represents the intersection of this range with another"""
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

    def is_empty(self):
        """Returns true on any empty range."""
        return (self.start is not None and
                self.end is not None and
                self.start == self.end and
                self.inclusivity != TimeRange.INCLUSIVE)
