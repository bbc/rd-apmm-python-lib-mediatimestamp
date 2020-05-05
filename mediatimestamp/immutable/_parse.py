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

from typing import Tuple

from ..exceptions import TsValueError
from ..constants import MAX_NANOSEC


def _parse_seconds_fraction(frac: str) -> int:
    """ Parse the fraction part of a timestamp seconds, using maximum 9 digits
    Returns the nanoseconds
    """
    ns = 0
    mult = MAX_NANOSEC
    for c in frac:
        if c < '0' or c > '9' or int(mult) < 1:
            break
        mult = mult // 10
        ns += mult * int(c)
    return ns


def _parse_iso8601(iso8601: str) -> Tuple[int, int, int, int, int, int, int]:
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
