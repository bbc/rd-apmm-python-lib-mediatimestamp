# Copyright 2017 British Broadcasting Corporation
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

"""This library provides a class TimeOffset which stores a signed time difference value with nanosecond precision.

It also provides a class Timestamp which is a descendent of TimeOffset which represents a positive time offset since
the epoch (ie. 1970-01-01T00:00:00.000000000Z)

These data types are of use in a number of situations, but particularly for code that will handle PTP timestamps, which
are normally stored in this fashion.
"""

from .exceptions import TsValueError
from .immutable import (
    TimeOffset, SupportsMediaTimeOffset, mediatimeoffset,
    Timestamp, SupportsMediaTimestamp, mediatimestamp,
    TimeRange, SupportsMediaTimeRange, mediatimerange)

from .count_range import CountRange
from .time_value import TimeValue, TimeValueConstructTypes
from .time_value_range import TimeValueRange, RangeConstructionTypes, RangeTypes

__all__ = [
    "TsValueError",
    "TimeOffset", "SupportsMediaTimeOffset", "mediatimeoffset",
    "Timestamp", "SupportsMediaTimestamp", "mediatimestamp",
    "TimeRange", "SupportsMediaTimeRange", "mediatimerange",
    "CountRange",
    "TimeValue", "TimeValueConstructTypes",
    "TimeValueRange", "RangeConstructionTypes", "RangeTypes"]
