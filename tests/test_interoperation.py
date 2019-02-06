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

import unittest

from mediatimestamp.bases import BaseTimeOffset
from mediatimestamp.immutable import TimeOffset
from mediatimestamp.mutable import TimeOffset as MutableTimeOffset

from mediatimestamp.hypothesis.strategies import immutabletimeoffsets
from hypothesis import given, assume


class TestInteroperability(unittest.TestCase):

    def test_both_offsets_descend_from_base(self):
        self.assertTrue(issubclass(TimeOffset, BaseTimeOffset))
        self.assertTrue(issubclass(MutableTimeOffset, BaseTimeOffset))

    @given(immutabletimeoffsets())
    def test_mutable_and_immutable_offsets_compare_as_equal(self, offs):
        mut = MutableTimeOffset.from_timeoffset(offs)
        self.assertEqual(offs, mut)
        self.assertEqual(mut, offs)

    @given(immutabletimeoffsets(), immutabletimeoffsets())
    def test_mutable_and_immutable_offsets_compare_as_unequal_when_unequal(self, offs0, offs1):
        assume(offs0 < offs1)
        mut = MutableTimeOffset.from_timeoffset(offs1)
        self.assertLess(offs0, mut)
        self.assertGreater(mut, offs0)

        mut = MutableTimeOffset.from_timeoffset(offs0)
        self.assertLess(mut, offs1)
        self.assertGreater(offs1, mut)
