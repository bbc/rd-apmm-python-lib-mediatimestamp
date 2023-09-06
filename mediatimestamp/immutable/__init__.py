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

"""This library provides a class Timestamp which stores an immutable signed time difference value with nanosecond
precision.

The Timestamp can represent an immutable time offset since the epoch (ie. 1970-01-01T00:00:00.000000000Z)

This library also includes an immutable TimeRange object which stores a range between two Timestamps.

These data types are of use in a number of situations, but particularly for code that will handle PTP timestamps, which
are normally stored in this fashion.
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
