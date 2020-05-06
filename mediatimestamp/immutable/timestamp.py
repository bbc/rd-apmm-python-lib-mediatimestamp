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

import calendar
import time
import re
from datetime import datetime
from dateutil import tz
from fractions import Fraction
from typing import Tuple, Optional, cast, TYPE_CHECKING
from typing_extensions import Protocol, runtime_checkable

from ..constants import UTC_LEAP
from ..exceptions import TsValueError

from ._parse import _parse_iso8601
from ._types import RationalTypes
from .timeoffset import TimeOffset, TimeOffsetConstructionType, mediatimeoffset

if TYPE_CHECKING:
    from .timerange import TimeRange  # noqa: F401

__all__ = ["Timestamp", "SupportsMediaTimestamp", "mediatimestamp"]


@runtime_checkable
class SupportsMediaTimestamp (Protocol):
    def __mediatimestamp__(self) -> "Timestamp":
        ...


def mediatimestamp(v: SupportsMediaTimestamp) -> "Timestamp":
    """This method can be called on any object which supports the __mediatimestamp__ magic method
    and also on a Timestamp. It will always return a Timestamp or raise a ValueError.
    """
    if isinstance(v, Timestamp):
        return v
    elif hasattr(v, "__mediatimestamp__"):
        return v.__mediatimestamp__()
    else:
        raise ValueError("{!r} cannot be converted to a mediatimestamp.Timestamp".format(v))


class Timestamp(TimeOffset):
    """A nanosecond precision immutable timestamp."""
    def __init__(self, sec: int = 0, ns: int = 0, sign: int = 1):
        super(Timestamp, self).__init__(sec, ns, sign)

    def __setattr__(self, name: str, value: object) -> None:
        raise TsValueError("Cannot assign to an immutable Timestamp")

    def __mediatimeoffset__(self) -> TimeOffset:
        return self

    def __mediatimestamp__(self) -> "Timestamp":
        return self

    def __mediatimerange__(self) -> "TimeRange":
        from .timerange import TimeRange  # noqa: F811

        return TimeRange.from_single_timestamp(self)

    @classmethod
    def get_time(cls, *, force_pure_python=False) -> "Timestamp":
        """The force_pure_python keyword only argument is ignored."""
        utc_time = time.time()
        return cls.from_utc(int(utc_time), int(utc_time*cls.MAX_NANOSEC) - int(utc_time)*cls.MAX_NANOSEC)

    @classmethod
    def from_timeoffset(cls, toff: TimeOffsetConstructionType) -> "Timestamp":
        toff = mediatimeoffset(toff)
        return cls(sec=toff.sec, ns=toff.ns, sign=toff.sign)

    @classmethod
    def from_sec_frac(cls, ts_str: str) -> "Timestamp":
        return cast(Timestamp, super(Timestamp, cls).from_sec_frac(ts_str))

    @classmethod
    def from_tai_sec_frac(cls, ts_str: str) -> "Timestamp":
        return cls.from_sec_frac(ts_str)

    @classmethod
    def from_sec_nsec(cls, ts_str: str) -> "Timestamp":
        return cast(Timestamp, super(Timestamp, cls).from_sec_nsec(ts_str))

    @classmethod
    def from_tai_sec_nsec(cls, ts_str: str) -> "Timestamp":
        return cls.from_sec_nsec(ts_str)

    @classmethod
    def from_datetime(cls, dt: datetime) -> "Timestamp":
        minTs = datetime.fromtimestamp(0, tz.gettz('UTC'))
        utcdt = dt.astimezone(tz.gettz('UTC'))
        seconds = int((utcdt - minTs).total_seconds())
        nanoseconds = utcdt.microsecond * 1000

        return cls.from_utc(seconds, nanoseconds, False)

    @classmethod
    def from_iso8601_utc(cls, iso8601utc: str) -> "Timestamp":
        if not iso8601utc.endswith('Z'):
            raise TsValueError("missing 'Z' at end of ISO 8601 UTC format")
        year, month, day, hour, minute, second, ns = _parse_iso8601(iso8601utc[:-1])
        gmtuple = (year, month, day, hour, minute, second - (second == 60))
        secs_since_epoch = calendar.timegm(gmtuple)
        return cls.from_utc(secs_since_epoch, ns, (second == 60))

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
    def from_str(cls, ts_str: str, *, force_pure_python=False) -> "Timestamp":
        """Parse a string as a TimeStamp

        Accepts SMPTE timelabel, ISO 8601 UTC, second:nanosecond and second.fraction formats, along with "now" to mean
        the current time.

        The force_pure_python keyword only argument is ignored.
        """
        if 'F' in ts_str:
            return cls.from_smpte_timelabel(ts_str)
        elif 'T' in ts_str:
            return cls.from_iso8601_utc(ts_str)
        elif ts_str.strip() == 'now':
            return cls.get_time()
        else:
            return cast(Timestamp, super(Timestamp, cls).from_str(ts_str))

    @classmethod
    def from_count(cls, count: int, rate_num: RationalTypes, rate_den: RationalTypes = 1) -> "Timestamp":
        return cast(Timestamp, super(Timestamp, cls).from_count(count, rate_num, rate_den))

    @classmethod
    def from_utc(cls, utc_sec: int, utc_ns: int, is_leap: bool = False) -> "Timestamp":
        leap_sec = 0
        for tbl_sec, tbl_tai_sec_minus_1 in UTC_LEAP:
            if utc_sec >= tbl_sec:
                leap_sec = (tbl_tai_sec_minus_1 + 1) - tbl_sec
                break
        return cls(sec=utc_sec+leap_sec+is_leap, ns=utc_ns)

    def get_leap_seconds(self) -> int:
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

    def to_tai_sec_nsec(self) -> str:
        return self.to_sec_nsec()

    def to_tai_sec_frac(self, fixed_size: bool = False) -> str:
        return self.to_sec_frac(fixed_size=fixed_size)

    def to_datetime(self) -> datetime:
        sec, nsec, leap = self.to_utc()
        dt = datetime.fromtimestamp(sec, tz.gettz('UTC'))
        dt = dt.replace(microsecond=int(round(nsec/1000)))

        return dt

    def to_utc(self) -> Tuple[int, int, bool]:
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

    def to_iso8601_utc(self) -> str:
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
                    rate.numerator, rate.denominator,
                    utc_sign_char, utc_offset_hour, utc_offset_min,
                    tai_sign_char, abs(tai_offset))

    def normalise(self,
                  rate_num: RationalTypes,
                  rate_den: RationalTypes = 1,
                  rounding: "TimeOffset.Rounding" = TimeOffset.ROUND_NEAREST) -> "Timestamp":
        """Return the nearest Timestamp to self which represents an integer number of samples at the given rate.

        :param rate_num: Rate numerator
        :param rate_den: Rate denominator
        :param rounding: How to round, if set to TimeOffset.ROUND_DOWN (resp. TimeOffset.ROUND_UP) this method will only
                         return a TimeOffset less than or equal to this one (resp. greater than or equal to).
        """
        return self.from_count(self.to_count(rate_num, rate_den, rounding), rate_num, rate_den)

    def __add__(self, other_in: TimeOffsetConstructionType) -> "Timestamp":
        return cast(Timestamp, super().__add__(other_in))

    def __iadd__(self, other_in: TimeOffsetConstructionType) -> "Timestamp":
        return cast(Timestamp, super().__add__(other_in))

    def __isub__(self, other_in: TimeOffsetConstructionType) -> "Timestamp":
        return cast(Timestamp, super().__isub__(other_in))

    def __mul__(self, anint: int) -> "Timestamp":
        return cast(Timestamp, super().__mul__(anint))

    def __rmul__(self, anint: int) -> "Timestamp":
        return cast(Timestamp, super().__rmul__(anint))
