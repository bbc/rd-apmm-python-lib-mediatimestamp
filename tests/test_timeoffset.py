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

import unittest
from fractions import Fraction

from copy import deepcopy

from mediatimestamp.immutable import TimeOffset, TsValueError, SupportsMediaTimeOffset, mediatimeoffset


class TestTimeOffset(unittest.TestCase):
    def test_supportsmediatimeoffset(self):
        to = TimeOffset()
        self.assertIsInstance(to, SupportsMediaTimeOffset)

        class _convertable(object):
            def __mediatimeoffset__(self) -> TimeOffset:
                return TimeOffset()

        c = _convertable()
        self.assertIsInstance(c, SupportsMediaTimeOffset)

        self.assertEqual(to, mediatimeoffset(to))
        self.assertEqual(to, mediatimeoffset(c))

    def test_MAX_NANOSEC(self):
        self.assertEqual(TimeOffset.MAX_NANOSEC, 1000000000)

    def test_from_timeoffset(self):
        """This tests that TimeOffsets can be created with a variety of values."""
        tests_ts = [
            (TimeOffset.from_timeoffset(TimeOffset(0, 0)), TimeOffset(0, 0)),
            (TimeOffset.from_timeoffset(TimeOffset(1001, 0)), TimeOffset(1001, 0)),
            (TimeOffset.from_timeoffset(TimeOffset(1001, 1001)), TimeOffset(1001, 1001)),
            ]

        for t in tests_ts:
            with self.subTest(t=t):
                self.assertEqual(t[0], t[1])

    def test_normalise(self):
        tests_ts = [
            (TimeOffset(0, 0), Fraction(30000, 1001), TimeOffset.ROUND_NEAREST,
             TimeOffset(0, 0)),
            (TimeOffset(1001, 0), Fraction(30000, 1001), TimeOffset.ROUND_NEAREST,
             TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000), Fraction(30000, 1001), TimeOffset.ROUND_NEAREST,
             TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1), Fraction(30000, 1001), TimeOffset.ROUND_NEAREST,
             TimeOffset(1001, 1001.0/30000*1000000000)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000, -1), Fraction(30000, 1001), TimeOffset.ROUND_NEAREST,
             TimeOffset(1001, 0, -1)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1, -1), Fraction(30000, 1001), TimeOffset.ROUND_NEAREST,
             TimeOffset(1001, 1001.0/30000*1000000000, -1)),
            (TimeOffset(1521731233, 320000000), Fraction(25, 3), TimeOffset.ROUND_NEAREST,
             TimeOffset(1521731233, 320000000)),
            (TimeOffset(0, 0), Fraction(30000, 1001), TimeOffset.ROUND_UP,
             TimeOffset(0, 0)),
            (TimeOffset(1001, 0), Fraction(30000, 1001), TimeOffset.ROUND_UP,
             TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000), Fraction(30000, 1001), TimeOffset.ROUND_UP,
             TimeOffset(1001, 1001.0/30000*1000000000)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1), Fraction(30000, 1001), TimeOffset.ROUND_UP,
             TimeOffset(1001, 1001.0/30000*1000000000)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000, -1), Fraction(30000, 1001), TimeOffset.ROUND_UP,
             TimeOffset(1001, 0, -1)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1, -1), Fraction(30000, 1001), TimeOffset.ROUND_UP,
             TimeOffset(1001, 0, -1)),
            (TimeOffset(1521731233, 320000000), Fraction(25, 3), TimeOffset.ROUND_UP,
             TimeOffset(1521731233, 320000000)),
            (TimeOffset(0, 0), Fraction(30000, 1001), TimeOffset.ROUND_DOWN,
             TimeOffset(0, 0)),
            (TimeOffset(1001, 0), Fraction(30000, 1001), TimeOffset.ROUND_DOWN,
             TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000), Fraction(30000, 1001), TimeOffset.ROUND_DOWN,
             TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1), Fraction(30000, 1001), TimeOffset.ROUND_DOWN,
             TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000, -1), Fraction(30000, 1001), TimeOffset.ROUND_DOWN,
             TimeOffset(1001, 1001.0/30000*1000000000, -1)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1, -1), Fraction(30000, 1001), TimeOffset.ROUND_DOWN,
             TimeOffset(1001, 1001.0/30000*1000000000, -1)),
            (TimeOffset(1521731233, 320000000), Fraction(25, 3), TimeOffset.ROUND_DOWN,
             TimeOffset(1521731233, 320000000)),
        ]

        n = 0
        for (input, rate, rounding, expected) in tests_ts:
            # Nb. subTest will add a printout of all its kwargs to any error message generated
            # by a failure within it. The variable n is being used here to ensure that the index
            # of the current test within tests_ts is printed on any failure. (Nb. only works with
            # python3 unittest test runner)
            with self.subTest(test_data_index=n,
                              input=input,
                              rate=rate,
                              rounding=rounding,
                              expected=expected):
                n += 1
                r = input.normalise(rate.numerator, rate.denominator, rounding=rounding)
                self.assertEqual(r, expected,
                                 msg=("{!r}.normalise({}, {}, rounding={}) == {!r}, expected {!r}"
                                      .format(input, rate.numerator, rate.denominator, rounding, r, expected)))

    def test_hash(self):
        self.assertEqual(hash(TimeOffset(0, 0)), hash(TimeOffset(0, 0)))
        self.assertNotEqual(hash(TimeOffset(0, 0)), hash(TimeOffset(0, 1)))

    def test_subsec(self):
        """This tests that TimeOffsets can be converted to millisec, nanosec, and microsec values."""
        tests_ts = [
            (TimeOffset(1, 1000000), "to_millisec", (), 1001),
            (TimeOffset(1, 1000), "to_microsec", (), 1000001),
            (TimeOffset(1, 1), "to_nanosec", (), 1000000001),
            (TimeOffset, 'from_millisec', (1001,), TimeOffset(1, 1000000)),
            (TimeOffset, 'from_microsec', (1000001,), TimeOffset(1, 1000)),
            (TimeOffset, 'from_nanosec', (1000000001,), TimeOffset(1, 1)),
            (TimeOffset(1, 500000), 'to_millisec', (TimeOffset.ROUND_DOWN,), 1000),
            (TimeOffset(1, 500000), 'to_millisec', (TimeOffset.ROUND_NEAREST,), 1001),
            (TimeOffset(1, 499999), 'to_millisec', (TimeOffset.ROUND_NEAREST,), 1000),
            (TimeOffset(1, 500000), 'to_millisec', (TimeOffset.ROUND_UP,), 1001),
            (TimeOffset(1, 500000, -1), 'to_millisec', (TimeOffset.ROUND_DOWN,), -1001),
            (TimeOffset(1, 500000, -1), 'to_millisec', (TimeOffset.ROUND_NEAREST,), -1001),
            (TimeOffset(1, 499999, -1), 'to_millisec', (TimeOffset.ROUND_NEAREST,), -1000),
            (TimeOffset(1, 500000, -1), 'to_millisec', (TimeOffset.ROUND_UP,), -1000)
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = getattr(t[0], t[1])(*t[2])
                self.assertEqual(r, t[3],
                                 msg="{!r}.{}{!r} == {!r}, expected {!r}".format(t[0], t[1], t[2], r, t[3]))

    def test_interval_frac(self):
        """This tests that TimeOffsets can be converted to interval fractions."""
        tests_ts = [
            ((50, 1, 1), TimeOffset(0, 20000000)),
            ((50, 1, 2), TimeOffset(0, 10000000))
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = TimeOffset.get_interval_fraction(*t[0])
                self.assertEqual(r, t[1],
                                 msg=("TimeOffset.get_interval_fraction{!r} == {!r}, expected {!r}"
                                      .format(t[0], r, t[1])))

        bad_params = [(0, 1, 1),
                      (50, 0, 1),
                      (50, 1, 0)]

        for params in bad_params:
            with self.assertRaises(TsValueError,
                                   msg=("TimeOffset.get_interval_fraction{!r} should have raised TsValueError exception"
                                        .format(params))):
                TimeOffset.get_interval_fraction(*params)

    def test_from_sec_frac(self):
        """This tests that timeoffsets can be instantiated from fractional second values."""
        tests_ts = [
            (("1.000000001",), TimeOffset(1, 1)),
            (("-1.000000001",), TimeOffset(1, 1, sign=-1)),
            (("1.000001POTATO",), TimeOffset(1, 1000)),
            (("1",), TimeOffset(1, 0)),
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = TimeOffset.from_sec_frac(*t[0])
                self.assertEqual(r, t[1],
                                 msg="TimeOffset.from_sec_frac{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

        bad_params = [("0.0.1",), ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.from_sec_frac(*params)

    def test_from_sec_nsec(self):
        """This tests that time offsets can be created from second:nanosecond pairs."""
        tests_ts = [
            (("1:1",), TimeOffset(1, 1)),
            (("-1:1",), TimeOffset(1, 1, sign=-1)),
            (("1",), TimeOffset(1, 0)),
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = TimeOffset.from_sec_nsec(*t[0])
                self.assertEqual(r, t[1],
                                 msg="TimeOffset.from_sec_nsec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

        bad_params = [("0:0:1",), ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.from_sec_nsec(*params)

    def test_from_count(self):
        """This tests that time offsets can be created from counts at a specified frequency."""
        tests_ts = [
            ((1, 50, 1), TimeOffset(0, 20000000)),
            ((75, 50, 1), TimeOffset(1, 500000000)),
            ((-75, 50, 1), TimeOffset(1, 500000000, -1))
        ]

        for t in tests_ts:
            r = TimeOffset.from_count(*t[0])
            self.assertEqual(r, t[1],
                             msg="TimeOffset.from_count{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

        bad_params = [(1, 0, 1),
                      (1, 1, 0)]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.from_count(*params)

    def test_from_millisec(self):
        """This tests that time offsets can be created from millisecond values."""
        tests_ts = [
            ((1,), TimeOffset(0, 1000000)),
            ((1000,), TimeOffset(1, 0)),
            ((-1,), TimeOffset(0, 1000000, -1))
        ]

        for t in tests_ts:
            r = TimeOffset.from_millisec(*t[0])
            self.assertEqual(r, t[1],
                             msg="TimeOffset.from_millisec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_from_microsec(self):
        """This tests that time offsets can be created from microsecond values."""
        tests_ts = [
            ((1,), TimeOffset(0, 1000)),
            ((1000000,), TimeOffset(1, 0)),
            ((-1,), TimeOffset(0, 1000, -1))
        ]

        for t in tests_ts:
            r = TimeOffset.from_microsec(*t[0])
            self.assertEqual(r, t[1],
                             msg="TimeOffset.from_microsec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_from_nanosec(self):
        """This tests that time offsets can be created from nanosecond values."""
        tests_ts = [
            ((1,), TimeOffset(0, 1)),
            ((1000000000,), TimeOffset(1, 0)),
            ((-1,), TimeOffset(0, 1, -1))
        ]

        for t in tests_ts:
            r = TimeOffset.from_nanosec(*t[0])
            self.assertEqual(r, t[1],
                             msg="TimeOffset.from_nanosec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_set_value(self):
        """This tests that time offsets cannot have their value set."""
        tests_ts = [
            (TimeOffset(0, 0), TimeOffset(0, 1), (0, 1)),
            (TimeOffset(0, 0), TimeOffset(1, 0), (1, 0)),
            (TimeOffset(0, 0), TimeOffset(0, 1, -1), (0, 1, -1))
        ]

        for t in tests_ts:
            ts = deepcopy(t[0])
            with self.assertRaises(AttributeError):
                ts.set_value(*t[2])
            self.assertEqual(ts, t[0])

    def test_to_count(self):
        """This tests that time offsets can be converted to counts at particular frequencies."""
        tests_ts = [
            (TimeOffset(0, 20000000), (50, 1), 1),
            (TimeOffset(1, 500000000), (50, 1), 75),
            (TimeOffset(1, 500000000, -1), (50, 1), -75),
            # below .5 frame
            (TimeOffset(100, 29999999), (50, 1), 100 * 50 + 1),
            # at .5 frame
            (TimeOffset(100, 30000000), (50, 1), 100 * 50 + 2),
            # above .5 frame
            (TimeOffset(100, 30000001), (50, 1), 100 * 50 + 2),
            # below negative .5 frame
            (TimeOffset(100, 9999999), (50, 1), 100 * 50),
            # at negative .5 frame
            (TimeOffset(100, 10000000), (50, 1), 100 * 50 + 1),
            # above negative .5 frame
            (TimeOffset(100, 10000001), (50, 1), 100 * 50 + 1),
            # below .5 frame, round up
            (TimeOffset(100, 29999999), (50, 1, TimeOffset.ROUND_UP), 100 * 50 + 2),
            # at .5 frame, round down
            (TimeOffset(100, 30000000), (50, 1, TimeOffset.ROUND_DOWN), 100 * 50 + 1),
            # above .5 frame, round down
            (TimeOffset(100, 30000001), (50, 1, TimeOffset.ROUND_DOWN), 100 * 50 + 1),
            # below .5 frame, round up
            (TimeOffset(100, 29999999, -1), (50, 1, TimeOffset.ROUND_DOWN), -100 * 50 - 2),
            # at .5 frame, round down
            (TimeOffset(100, 30000000, -1), (50, 1, TimeOffset.ROUND_UP), -100 * 50 - 1),
            # above .5 frame, round down
            (TimeOffset(100, 30000001, -1), (50, 1, TimeOffset.ROUND_UP), -100 * 50 - 1),
        ]

        for t in tests_ts:
            r = t[0].to_count(*t[1])
            self.assertEqual(r, t[2],
                             msg="{!r}.to_count{!r} == {!r}, expected {!r}".format(t[0], t[1], r, t[2]))

        bad_params = [(1, 0),
                      (0, 1)]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset(0, 0).to_count(*params)

    def test_to_microsec(self):
        """This tests that time offsets can be converted to microsecond values."""
        tests_ts = [
            (TimeOffset(0, 1000), (), 1),
            (TimeOffset(1, 1000000), (), 1001000),
            (TimeOffset(1, 1000000, -1), (), -1001000),
            # below .5 us
            (TimeOffset(100, 1499), (), 100 * 1000000 + 1),
            # at .5 us
            (TimeOffset(100, 1500), (), 100 * 1000000 + 2),
            # above .5 us
            (TimeOffset(100, 1501), (), 100 * 1000000 + 2),
            # below .5 us, round up
            (TimeOffset(100, 1499), (TimeOffset.ROUND_UP,), 100 * 1000000 + 2),
            # at .5 us, round up
            (TimeOffset(100, 1500), (TimeOffset.ROUND_UP,), 100 * 1000000 + 2),
            # above .5 us, round up
            (TimeOffset(100, 1501), (TimeOffset.ROUND_UP,), 100 * 1000000 + 2),
            # below .5 us, round down
            (TimeOffset(100, 1499), (TimeOffset.ROUND_DOWN,), 100 * 1000000 + 1),
            # at .5 us, round down
            (TimeOffset(100, 1500), (TimeOffset.ROUND_DOWN,), 100 * 1000000 + 1),
            # above .5 us, round down
            (TimeOffset(100, 1501), (TimeOffset.ROUND_DOWN,), 100 * 1000000 + 1),
            # below .5 us, round down
            (TimeOffset(100, 1499, -1), (TimeOffset.ROUND_DOWN,), -100 * 1000000 - 2),
            # at .5 us, round down
            (TimeOffset(100, 1500, -1), (TimeOffset.ROUND_DOWN,), -100 * 1000000 - 2),
            # above .5 us, round down
            (TimeOffset(100, 1501, -1), (TimeOffset.ROUND_DOWN,), -100 * 1000000 - 2),
            # below .5 us, round up
            (TimeOffset(100, 1499, -1), (TimeOffset.ROUND_UP,), -100 * 1000000 - 1),
            # at .5 us, round up
            (TimeOffset(100, 1500, -1), (TimeOffset.ROUND_UP,), -100 * 1000000 - 1),
            # above .5 us, round up
            (TimeOffset(100, 1501, -1), (TimeOffset.ROUND_UP,), -100 * 1000000 - 1),
        ]

        for t in tests_ts:
            r = t[0].to_microsec(*t[1])
            self.assertEqual(r, t[2],
                             msg="{!r}.to_microsec{!r} == {!r}, expected {!r}".format(t[0], t[1], r, t[2]))

    def test_abs(self):
        """This tests that negative time offsets can be converted to positive ones using abs."""
        tests_ts = [
            (TimeOffset(10, 1), TimeOffset(10, 1)),
            (TimeOffset(10, 1, -1), TimeOffset(10, 1))
        ]

        for t in tests_ts:
            r = abs(t[0])
            self.assertEqual(r, t[1],
                             msg="abs({!r}) == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_average(self):
        """This tests that time offsets can be averaged."""
        toff1 = TimeOffset(11, 976)
        toff2 = TimeOffset(21, 51)
        toff_avg = (toff1 * 49 + toff2) // 50
        avg = int((toff1.to_nanosec() * 49 + toff2.to_nanosec()) // 50)
        self.assertEqual(avg, toff_avg.to_nanosec())

    def test_cast(self):
        """This tests that addition and subtraction of TimeOffsets and integers or floats works as expected."""
        tests_ts = [
            (TimeOffset(10, 1), '+',  1, TimeOffset(11, 1)),
            (TimeOffset(10, 1), '-', 1, TimeOffset(9, 1)),
            (TimeOffset(10, 1), '+', 1.5, TimeOffset(11, 500000001)),
            (TimeOffset(10, 1), '-', 1.5, TimeOffset(8, 500000001)),
        ]

        for t in tests_ts:
            if t[1] == '+':
                r = t[0] + t[2]
            else:
                r = t[0] - t[2]
            self.assertEqual(r, t[3],
                             msg="{!r} {} {!r} == {!r}, expected {}".format(t[0], t[1], t[2], r, t[3]))

        self.assertEqual(TimeOffset(8, 500000000), 8.5)
        self.assertGreater(TimeOffset(8, 500000000), 8)
        self.assertLess(TimeOffset(8, 500000000), 8.6)
        self.assertNotEqual(TimeOffset(8, 500000000), 8.6)

    def test_eq(self):
        """Test some equality operations"""
        self.assertEqual(TimeOffset(10, 1), TimeOffset(10, 1))
        self.assertNotEqual(TimeOffset(10, 1), TimeOffset(-10, 1))
        self.assertNotEqual(TimeOffset(0, 1), TimeOffset(0, -1))
        self.assertNotEqual(TimeOffset(0, 1), None)
        self.assertEqual(TimeOffset(0, 500000000), 0.5)
        self.assertNotEqual(TimeOffset(0, 1), "0:1")

    def test_str(self):
        """This tests that the str function turns time offsets into second:nanosecond pairs."""
        tests_ts = [
            (str(TimeOffset(10, 1)), "10:1"),
            (str(TimeOffset(10, 1, -1)), "-10:1"),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])
