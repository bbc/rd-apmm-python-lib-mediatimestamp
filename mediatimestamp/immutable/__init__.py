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

"""This library provides a class TimeOffset which stores an immutable signed time difference value with nanosecond
precision.

It also provides a class Timestamp which is a descendent of TimeOffset which represents an immutable time offset since
the epoch (ie. 1970-01-01T00:00:00.000000000Z)

And finally it includes an immutable TimeRange object which stores a range between two Timestamps.

These data types are of use in a number of situations, but particularly for code that will handle PTP timestamps, which
are normally stored in this fashion.



Expected Logic for binary operations on timestamps and time offsets:

Timestamp and TimeOffset objects can be added and subtracted. The type of the final result depends upon the order and
type of the operands

TS + TO = TS
TS + TS = TS (treats 2nd TS as TO)
TO + TS = TS
TO + TO = TO

TS - TO = TS
TS - TS = TO
TO - TS = TO (treats TS as TO)
TO - TO = TO

+= and -= always give the same result type as the first operand

Instances of TimeOffset can always be multiplied or divided by integers and floats and always give
another TimeOffset as a result.

An instance of Timestamp multiplied by integers or floats will be treated as an instance of TimeOffset
"""

from .timeoffset import TimeOffset, SupportsMediaTimeOffset, mediatimeoffset
from .timestamp import Timestamp, SupportsMediaTimestamp, mediatimestamp
from .timerange import TimeRange, SupportsMediaTimeRange, mediatimerange
from ..exceptions import TsValueError


__all__ = [
    "TimeOffset", "SupportsMediaTimeOffset", "mediatimeoffset",
    "Timestamp", "SupportsMediaTimestamp", "mediatimestamp",
    "TimeRange", "SupportsMediaTimeRange", "mediatimerange",
    "TsValueError"]
