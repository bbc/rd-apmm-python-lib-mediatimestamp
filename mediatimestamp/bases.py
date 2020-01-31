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

__all__ = ["BaseTimeOffset", "BaseTimeRange"]

from typing import Optional
from abc import ABCMeta, abstractmethod


class BaseTimeOffset (object, metaclass=ABCMeta):
    """This class exists as an abstract base class for all TimeOffset and
    Timestamp classes. It exists mostly so that comparisons between mutable
    and immutable timestamps can be done even though the two are entirely
    different classes."""
    def __init__(self, sec: int = 0, ns: int = 0, sign: int = 1):
        self.sec: int
        self.ns: int
        self.sign: int

        self.__dict__['sec'] = int(sec)
        self.__dict__['ns'] = int(ns)
        self.__dict__['sign'] = int(sign)


class BaseTimeRange (object, metaclass=ABCMeta):
    """This class exists as an abstract base class for all TimeRange classes.
    It exists mostly so that comparisons between mutable and immutable
    timeranges can be done even though the two are entirely different
    classes."""

    class Inclusivity (int):
        def __and__(self, other: int) -> "BaseTimeRange.Inclusivity":
            return BaseTimeRange.Inclusivity(int(self) & int(other) & 0x3)

        def __or__(self, other: int) -> "BaseTimeRange.Inclusivity":
            return BaseTimeRange.Inclusivity((int(self) | int(other)) & 0x3)

        def __xor__(self, other: int) -> "BaseTimeRange.Inclusivity":
            return BaseTimeRange.Inclusivity((int(self) ^ int(other)) & 0x3)

        def __invert__(self) -> "BaseTimeRange.Inclusivity":
            return BaseTimeRange.Inclusivity((~int(self)) & 0x3)

    EXCLUSIVE = Inclusivity(0x0)
    INCLUDE_START = Inclusivity(0x1)
    INCLUDE_END = Inclusivity(0x2)
    INCLUSIVE = Inclusivity(0x3)

    def __init__(self,
                 start: Optional[BaseTimeOffset],
                 end: Optional[BaseTimeOffset],
                 inclusivity: "BaseTimeRange.Inclusivity"):
        self.start: Optional[BaseTimeOffset]
        self.end: Optional[BaseTimeOffset]
        self.inclusivity: BaseTimeRange.Inclusivity

        self.__dict__['start'] = start
        self.__dict__['end'] = end
        self.__dict__['inclusivity'] = inclusivity

    @abstractmethod
    def is_empty(self) -> bool:
        ...
