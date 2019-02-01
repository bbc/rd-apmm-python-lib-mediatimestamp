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

from __future__ import print_function
from __future__ import absolute_import

__all__ = ["TsValueError", "TimeOffset", "Timestamp", "TimeRange"]

from .exceptions import TsValueError


# THESE CONSTANTS ARE NOT PART OF THIS LIBRARY'S PIUBLIC INTERFACE
# The same values are made available by methods that are, such as
#
# TimeOffset.MAX_NANOSEC
#
# So use those instead. At some point these constants could go away without warning

from .constants import MAX_NANOSEC, MAX_SECONDS, UTC_LEAP  # noqa: F401


class BaseTimeOffset (object):
    def __init__(self, sec=0, ns=0, sign=1):
        self.__dict__['sec'] = int(sec)
        self.__dict__['ns'] = int(ns)
        self.__dict__['sign'] = int(sign)


class BaseTimeRange (object):
    def __init__(self, start, end, inclusivity):
        self.__dict__['start'] = start
        self.__dict__['end'] = end
        self.__dict__['inclusivity'] = inclusivity


# This is at the bottom because the above classes are needed before it can be imported
from .mutable import TimeOffset, Timestamp, TimeRange  # noqa: E402
