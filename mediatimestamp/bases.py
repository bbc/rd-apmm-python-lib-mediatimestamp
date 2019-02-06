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

from __future__ import print_function
from __future__ import absolute_import

__all__ = ["BaseTimeOffset", "BaseTimeRange"]


class BaseTimeOffset (object):
    """This class exists as an abstract base class for all TimeOffset and
    Timestamp classes. It exists mostly so that comparisons between mutable
    and immutable timestamps can be done even though the two are entirely
    different classes."""
    def __init__(self, sec=0, ns=0, sign=1):
        self.__dict__['sec'] = int(sec)
        self.__dict__['ns'] = int(ns)
        self.__dict__['sign'] = int(sign)


class BaseTimeRange (object):
    """This class exists as an abstract base class for all TimeRange classes.
    It exists mostly so that comparisons between mutable and immutable
    timeranges can be done even though the two are entirely different
    classes."""
    def __init__(self, start, end, inclusivity):
        self.__dict__['start'] = start
        self.__dict__['end'] = end
        self.__dict__['inclusivity'] = inclusivity
