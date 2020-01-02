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

from six import PY2

import unittest
import mock
import contextlib

from datetime import datetime
from dateutil import tz
from fractions import Fraction

from copy import deepcopy

from mediatimestamp.immutable import Timestamp, TimeOffset, TsValueError, TimeRange


@contextlib.contextmanager
def dummysubtest(*args, **kwargs):
    yield None


if PY2:
    BUILTINS = "__builtin__"
else:
    BUILTINS = "builtins"


class TestTimeOffset(unittest.TestCase):
    def setUp(self):
        if PY2:
            self.subTest = dummysubtest

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


class TestTimestamp(unittest.TestCase):
    def test_MAX_NANOSEC(self):
        self.assertEqual(Timestamp.MAX_NANOSEC, 1000000000)

    def test_get_time_pythonic(self):
        """This tests that the fallback pure python implementation of get_time works as expected."""
        test_ts = [
            (1512489451.0, Timestamp(1512489451 + 37, 0)),
            (1512489451.1, Timestamp(1512489451 + 37, 100000000))
            ]

        for t in test_ts:
            with mock.patch("time.time") as time:
                time.return_value = t[0]
                gottime = Timestamp.get_time(force_pure_python=True)
                self.assertEqual(gottime, t[1], msg="Times not equal, expected: %r, got %r" % (t[1], gottime))

    def test_iaddsub(self):
        """This tests integer addition and subtraction on timestamps."""
        ts = Timestamp(10, 0)
        ts += TimeOffset(1, 2)
        self.assertEqual(ts, Timestamp(11, 2))
        ts -= TimeOffset(1, 2)
        self.assertEqual(ts, Timestamp(10, 0))
        ts -= TimeOffset(100, 5)
        self.assertEqual(ts, Timestamp(90, 5, -1))

        ts = Timestamp(281474976710655, 999999999)
        ts += TimeOffset(0, 1)
        self.assertEqual(ts, Timestamp(281474976710655, 999999999))

        toff = TimeOffset(10, 0)
        toff -= TimeOffset(100, 0)
        self.assertEqual(toff, TimeOffset(90, 0, -1))

        toff = TimeOffset(10, 0)
        toff -= TimeOffset(0, 1)
        self.assertEqual(toff, TimeOffset(9, 999999999))

        toff = TimeOffset(10, 500000000)
        toff += TimeOffset(0, 500000000)
        self.assertEqual(toff, TimeOffset(11, 0))

        toff = TimeOffset(10, 500000000, -1)
        toff -= TimeOffset(0, 500000000)
        self.assertEqual(toff, TimeOffset(11, 0, -1))

        toff = TimeOffset(10, 0, -1)
        toff += TimeOffset(0, 500000000)
        self.assertEqual(toff, TimeOffset(9, 500000000, -1))

    def test_addsub(self):
        """This tests addition and subtraction on timestamps."""

        tests_ts = [
            (Timestamp(10, 0), '+', TimeOffset(1, 2), Timestamp(11, 2)),
            (Timestamp(11, 2), '-', TimeOffset(1, 2), Timestamp(10, 0)),
            (TimeOffset(11, 2), '-', TimeOffset(1, 2), TimeOffset(10, 0)),
            (Timestamp(10, 0), '-', TimeOffset(11, 2), Timestamp(1, 2, -1)),
            (TimeOffset(10, 0), '-', TimeOffset(11, 2), TimeOffset(1, 2, -1)),
            (TimeOffset(10, 0), '-', Timestamp(11, 2), TimeOffset(1, 2, -1)),
            (Timestamp(10, 0), '-', Timestamp(11, 2), TimeOffset(1, 2, -1)),
            (Timestamp(11, 2), '-', Timestamp(10, 0), TimeOffset(1, 2, 1)),
        ]

        for t in tests_ts:
            if t[1] == '+':
                r = t[0] + t[2]
            else:
                r = t[0] - t[2]

            self.assertEqual(r, t[3],
                             msg="{!r} {} {!r} = {!r}, expected {!r}".format(t[0], t[1], t[2], r, t[3]))
            self.assertEqual(type(r), type(t[3]),
                             msg=("type({!r} {} {!r}) == {!r}, expected {!r}"
                                  .format(t[0], t[1], t[2], type(r), type(t[3]))))

    def test_multdiv(self):
        """This tests multiplication and division on timestamps."""

        tests_ts = [
            (TimeOffset(10, 10), '*', 0, TimeOffset(0, 0)),
            (TimeOffset(10, 10), '*', 10, TimeOffset(100, 100)),
            (10, '*', TimeOffset(10, 10), TimeOffset(100, 100)),
            (TimeOffset(10, 10), '*', (-10), TimeOffset(100, 100, -1)),
            (TimeOffset(10, 10, -1), '*', 10, TimeOffset(100, 100, -1)),
            (TimeOffset(100, 100), '//', 10, TimeOffset(10, 10)),
            (TimeOffset(100, 100), '//', -10, TimeOffset(10, 10, -1)),
            (TimeOffset(100, 100, -1), '//', 10, TimeOffset(10, 10, -1)),
            (TimeOffset(281474976710654, 0), '//', 281474976710655, TimeOffset(0, 999999999)),
            (Timestamp(100, 100), '//', 10, TimeOffset(10, 10)),
            (TimeOffset(100, 100), '/', 10, TimeOffset(10, 10)),
            (TimeOffset(100, 100), '/', -10, TimeOffset(10, 10, -1)),
            (TimeOffset(100, 100, -1), '/', 10, TimeOffset(10, 10, -1)),
            (TimeOffset(281474976710654, 0), '/', 281474976710655, TimeOffset(0, 999999999)),
            (Timestamp(100, 100), '/', 10, TimeOffset(10, 10)),
            (Timestamp(10, 10), '*', 10, TimeOffset(100, 100)),
            (10, '*', Timestamp(10, 10), TimeOffset(100, 100)),
        ]

        for t in tests_ts:
            if t[1] == '*':
                r = t[0] * t[2]
            elif t[1] == '//':
                r = t[0] // t[2]
            else:
                r = t[0] / t[2]
            self.assertEqual(r, t[3],
                             msg="{!r} {} {!r} == {!r}, expected {!r}".format(t[0], t[1], t[2], r, t[3]))
            self.assertEqual(type(r), type(t[3]),
                             msg=("type({!r} {} {!r}) == {!r}, expected {!r}"
                                  .format(t[0], t[1], t[2], type(r), type(t[3]))))

    def test_compare(self):
        """This tests comparison of timestamps."""

        self.assertEqual(Timestamp(1, 2), Timestamp(1, 2))
        self.assertNotEqual(Timestamp(1, 2), Timestamp(1, 3))
        self.assertLess(Timestamp(1, 0), Timestamp(1, 2))
        self.assertLessEqual(Timestamp(1, 2), Timestamp(1, 2))
        self.assertGreater(Timestamp(2, 0), Timestamp(1, 0))
        self.assertGreaterEqual(Timestamp(2, 0), Timestamp(2, 0))
        self.assertNotEqual(Timestamp(2, 0), Timestamp(3, 0))
        self.assertEqual(Timestamp(2, 0), 2)
        self.assertGreater(Timestamp(2, 0), 1)
        self.assertLess(Timestamp(2, 0), 3)
        self.assertLess(TimeOffset(2, 0), 3)
        self.assertGreaterEqual(TimeOffset(1, 0, 1), TimeOffset(1, 0, -1))

    def test_invalid_str(self):
        """This tests that invalid strings fed into from_str raise exceptions."""

        tests_ts = [
            "a",
            "2015-02-17T12:53:48.5",
            "2015-02T12:53:48.5",
            "2015-02-17T12:53.5",
            "12:53:48.5"
        ]

        for t in tests_ts:
            try:
                Timestamp.from_str(t)
                self.assertTrue(False)
            except Exception:
                pass

    def test_invalid_int(self):
        """This tests that invalid int values fed into timestamp constructor get normalised."""

        tests_ts = [
            (Timestamp(-1, 0), Timestamp(1, 0, -1)),
            (Timestamp(281474976710656, 0), Timestamp(281474976710655, 999999999)),
            (Timestamp(0, 1000000000), Timestamp(1, 0)),
            (Timestamp(0, -1), Timestamp(0, 1, -1)),
            (Timestamp(5, -1000000007), Timestamp(3, 999999993))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_convert_str(self):
        """This tests that various string formats can be converted to timestamps."""

        tests_ts = [
            ("1:2", Timestamp(1, 2)),
            ("1.2", Timestamp(1, 200000000)),
            ("1", Timestamp(1, 0)),
            ("2015-02-17T12:53:48.5Z", Timestamp(1424177663, 500000000)),
            ("2015-02-17T12:53:48.000102003Z", Timestamp(1424177663, 102003))
        ]

        for t in tests_ts:
            ts = Timestamp.from_str(t[0])
            self.assertTrue(isinstance(ts, Timestamp))
            self.assertEqual(ts, t[1])

    def test_convert_sec_nsec(self):
        """This tests that the conversion to and from TAI second:nanosecond pairs works as expected."""

        tests_ts = [
            ("0:0", TimeOffset(0, 0), "0:0"),
            ("0:1", TimeOffset(0, 1), "0:1"),
            ("-0:1", TimeOffset(0, 1, -1), "-0:1"),
            ("5", TimeOffset(5, 0), "5:0"),
            ("5:1", TimeOffset(5, 1), "5:1"),
            ("-5:1", TimeOffset(5, 1, -1), "-5:1"),
            ("5:999999999", TimeOffset(5, 999999999), "5:999999999")
        ]

        for t in tests_ts:
            ts = TimeOffset.from_sec_nsec(t[0])
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_nsec()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))

    def test_ts_convert_tai_sec_nsec(self):
        """This tests that the conversion to and from TAI second:nanosecond pairs works as expected."""

        tests_ts = [
            ("0:0", Timestamp(0, 0), "0:0"),
            ("0:1", Timestamp(0, 1), "0:1"),
            ("-0:1", Timestamp(0, 1, -1), "-0:1"),
            ("5", Timestamp(5, 0), "5:0"),
            ("5:1", Timestamp(5, 1), "5:1"),
            ("-5:1", Timestamp(5, 1, -1), "-5:1"),
            ("5:999999999", Timestamp(5, 999999999), "5:999999999")
        ]

        for t in tests_ts:
            ts = Timestamp.from_sec_nsec(t[0])
            self.assertIsInstance(ts, Timestamp,
                                  msg=("Timestamp.from_sec_nsec({!r}) == {!r} not an instance of Timestamp"
                                       .format(t[0], ts)))
            self.assertEqual(
                ts,
                t[1],
                msg="Timestamp.from_sec_nsec({!r}) == {!r}, expected {!r}".format(t[0], ts, t[1]))
            ts_str = ts.to_sec_nsec()
            self.assertEqual(
                ts_str,
                t[2],
                msg="{!r}.to_sec_nsec() == {!r}, expected {!r}".format(ts, ts_str, t[2]))

    def test_convert_sec_frac(self):
        """This tests that the conversion to and from TAI seconds with fractional parts works as expected."""

        tests_ts = [
            ("0.0", TimeOffset(0, 0), "0.0"),
            ("0.1", TimeOffset(0, 1000000000 // 10), "0.1"),
            ("-0.1", TimeOffset(0, 1000000000 // 10, -1), "-0.1"),
            ("5", TimeOffset(5, 0), "5.0"),
            ("5.1", TimeOffset(5, 1000000000 // 10), "5.1"),
            ("-5.1", TimeOffset(5, 1000000000 // 10, -1), "-5.1"),
            ("5.10000000", TimeOffset(5, 1000000000 // 10), "5.1"),
            ("5.123456789", TimeOffset(5, 123456789), "5.123456789"),
            ("5.000000001", TimeOffset(5, 1), "5.000000001"),
            ("5.0000000001", TimeOffset(5, 0), "5.0")
        ]

        for t in tests_ts:
            ts = TimeOffset.from_sec_frac(t[0])
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_frac()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))

    def test_ts_convert_tai_sec_frac(self):
        """This tests that the conversion to and from TAI seconds with fractional parts works as expected."""

        tests_ts = [
            ("0.0", Timestamp(0, 0), "0.0"),
            ("0.1", Timestamp(0, 1000000000 // 10), "0.1"),
            ("-0.1", Timestamp(0, 100000000, -1), "-0.1"),
            ("5", Timestamp(5, 0), "5.0"),
            ("5.1", Timestamp(5, 1000000000 // 10), "5.1"),
            ("-5.1", Timestamp(5, 100000000, -1), "-5.1"),
            ("5.10000000", Timestamp(5, 1000000000 // 10), "5.1"),
            ("5.123456789", Timestamp(5, 123456789), "5.123456789"),
            ("5.000000001", Timestamp(5, 1), "5.000000001"),
            ("5.0000000001", Timestamp(5, 0), "5.0")
        ]

        for t in tests_ts:
            ts = Timestamp.from_sec_frac(t[0])
            self.assertIsInstance(ts, Timestamp,
                                  msg=("Timestamp.from_sec_frac({!r}) == {!r} not instance of Timestamp"
                                       .format(t[0], ts)))
            self.assertEqual(
                ts,
                t[1],
                msg="Timestamp.from_sec_frac({!r}) == {!r}, expected {!r}".format(t[0], ts, t[1]))
            ts_str = ts.to_sec_frac()
            self.assertEqual(
                ts_str,
                t[2],
                msg="{!r}.ts_to_sec_frac() == {!r}, expected {!r}".format(ts, ts_str, t[2]))

    def test_convert_iso_utc(self):
        """This tests that conversion to and from ISO date format UTC time works as expected."""

        tests = [
            (Timestamp(1424177663, 102003), "2015-02-17T12:53:48.000102003Z"),

            # the leap second is 23:59:60

            #   30 June 1972 23:59:59 (2287785599, first time): TAI= UTC + 10 seconds
            (Timestamp(78796809, 0), "1972-06-30T23:59:59.000000000Z"),

            #   30 June 1972 23:59:60 (2287785599,second time): TAI= UTC + 11 seconds
            (Timestamp(78796810, 0), "1972-06-30T23:59:60.000000000Z"),

            #   1  July 1972 00:00:00 (2287785600)      TAI= UTC + 11 seconds
            (Timestamp(78796811, 0), "1972-07-01T00:00:00.000000000Z"),

            (Timestamp(1341100833, 0), "2012-06-30T23:59:59.000000000Z"),
            (Timestamp(1341100834, 0), "2012-06-30T23:59:60.000000000Z"),
            (Timestamp(1341100835, 0), "2012-07-01T00:00:00.000000000Z"),

            (Timestamp(1341100835, 1), "2012-07-01T00:00:00.000000001Z"),
            (Timestamp(1341100835, 100000000), "2012-07-01T00:00:00.100000000Z"),
            (Timestamp(1341100835, 999999999), "2012-07-01T00:00:00.999999999Z"),

            (Timestamp(283996818, 0), "1979-01-01T00:00:00.000000000Z")  # 1979
        ]

        for t in tests:
            utc = t[0].to_iso8601_utc()
            self.assertEqual(utc, t[1])
            ts = Timestamp.from_iso8601_utc(t[1])
            self.assertEqual(ts, t[0])

        bad_params = [
            ("2012-07-01Y00:00:00.000000001Z",),
            ("2012-07~01T00:00:00.000000001Z",),
            ("2012-07-01T00:00:00.0000.0001Z",),
            ]

        for p in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_iso8601_utc(*p)

    def test_smpte_timelabel(self):
        """This tests that conversion to and from SMPTE time labels works correctly."""

        tests = [
            ("2015-01-23T12:34:56F00 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F01 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F02 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F28 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F29 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),

            ("2015-07-01T00:59:59F00 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:59F01 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:59F29 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:60F00 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:60F29 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T01:00:00F00 30000/1001 UTC+01:00 TAI-36", 30000, 1001, 60*60),
            ("2015-06-30T18:59:59F29 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-06-30T18:59:60F00 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-06-30T18:59:60F29 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-06-30T19:00:00F00 30000/1001 UTC-05:00 TAI-36", 30000, 1001, -5*60*60)
        ]

        for t in tests:
            ts = Timestamp.from_smpte_timelabel(t[0])
            self.assertEqual(t[0], ts.to_smpte_timelabel(t[1], t[2], t[3]))

        bad_params = [
            ("potato",),
            ("the quick brown fox jumps over the lazy dog",),
            ("",),
            ('\u3069\u3082\u3042\u308a\u304c\u3068\u3046\u3001\u30df\u30b9\u30bf\u30fc\u30fb\u30ed\u30dc\u30c8\u30fc',),
            ("About half nine on tuesday",),
            ("0315-13~35T25:63:60F56 50000/1002 UTC-25:35 TAY-2",),
            ]
        for p in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_smpte_timelabel(*p)

        bad_params = [
            (0, 1),
            (1, 0),
            ]
        for p in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp(0, 0).to_smpte_timelabel(*p)

        with mock.patch("time.timezone", 0):
            with mock.patch("time.localtime") as localtime:
                localtime.return_value.tm_isdst = 1
                ts = Timestamp.from_smpte_timelabel("2015-07-01T00:59:59F00 30000/1001 UTC+01:00 TAI-35")
                self.assertEqual("2015-07-01T00:59:59F00 30000/1001 UTC+01:00 TAI-35",
                                 ts.to_smpte_timelabel(30000, 1001))

    def test_from_datetime(self):
        """Conversion from python's datetime object."""

        tests = [
            (datetime(1970, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(0, 0)),
            (datetime(1983, 3, 29, 15, 45, 0, 0, tz.gettz('UTC')), Timestamp(417800721, 0)),
            (datetime(2017, 12, 5, 16, 33, 12, 196, tz.gettz('UTC')), Timestamp(1512491629, 196000)),
        ]

        for t in tests:
            self.assertEqual(Timestamp.from_datetime(t[0]), t[1])

    def test_to_datetime(self):
        """Conversion to python's datetime object."""

        tests = [
            (datetime(1970, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(0, 0)),
            (datetime(1983, 3, 29, 15, 45, 0, 0, tz.gettz('UTC')), Timestamp(417800721, 0)),
            (datetime(2017, 12, 5, 16, 33, 12, 196, tz.gettz('UTC')), Timestamp(1512491629, 196000)),
        ]

        for t in tests:
            self.assertEqual(t[0], t[1].to_datetime())

    def test_from_str(self):
        """Conversion from string formats."""

        tests = [
            ("2015-01-23T12:34:56F00 30000/1001 UTC-05:00 TAI-35", Timestamp(1422034531, 17100000)),
            ("2015-01-23T12:34:56.0Z", Timestamp(1422016531, 0)),
            ("now", Timestamp(0, 0)),
        ]

        for t in tests:
            with mock.patch("time.time", return_value=0.0):
                self.assertEqual(Timestamp.from_str(t[0], force_pure_python=True), t[1])

    def test_get_leap_seconds(self):
        """get_leap_seconds should return the correct number of leap seconds at any point in history."""

        tests = [
            (Timestamp(63072008, 999999999), 0),
            (Timestamp(63072009, 0), 10),
            (Timestamp(78796809, 999999999), 10),
            (Timestamp(78796810, 0), 11),
            (Timestamp(94694410, 999999999), 11),
            (Timestamp(94694411, 0), 12),
            (Timestamp(417800721, 0), 21),
            (Timestamp(773020827, 999999999), 28),
            (Timestamp(773020828, 0), 29),
            (Timestamp(1512491629, 0), 37),
        ]

        for t in tests:
            self.assertEqual(t[0].get_leap_seconds(), t[1])


class TestTimeRange (unittest.TestCase):
    def setUp(self):
        if PY2:
            self.subTest = dummysubtest

    def test_never(self):
        rng = TimeRange.never()

        self.assertNotIn(Timestamp(), rng)
        self.assertNotIn(Timestamp(326246400, 0), rng)
        self.assertNotIn(Timestamp(417799799, 999999999), rng)
        self.assertNotIn(Timestamp(417799800, 0), rng)
        self.assertNotIn(Timestamp(1530711653, 0), rng)
        self.assertNotIn(Timestamp(1530711653, 999999998), rng)
        self.assertNotIn(Timestamp(1530711653, 999999999), rng)
        self.assertNotIn(Timestamp(49391596800, 999999), rng)

        self.assertTrue(rng.is_empty())
        self.assertEqual(rng.to_sec_nsec_range(), "()")

    def test_eternity(self):
        alltime = TimeRange.eternity()

        self.assertIn(Timestamp(), alltime)
        self.assertIn(Timestamp(326246400, 0), alltime)
        self.assertIn(Timestamp(417799799, 999999999), alltime)
        self.assertIn(Timestamp(417799800, 0), alltime)
        self.assertIn(Timestamp(1530711653, 0), alltime)
        self.assertIn(Timestamp(1530711653, 999999998), alltime)
        self.assertIn(Timestamp(1530711653, 999999999), alltime)
        self.assertIn(Timestamp(49391596800, 999999), alltime)

        self.assertEqual(alltime.to_sec_nsec_range(), "_")

    def test_bounded_on_right_inclusive(self):
        rng = TimeRange.from_end(Timestamp(1530711653, 999999999))

        self.assertIn(Timestamp(), rng)
        self.assertIn(Timestamp(326246400, 0), rng)
        self.assertIn(Timestamp(417799799, 999999999), rng)
        self.assertIn(Timestamp(417799800, 0), rng)
        self.assertIn(Timestamp(1530711653, 0), rng)
        self.assertIn(Timestamp(1530711653, 999999998), rng)
        self.assertIn(Timestamp(1530711653, 999999999), rng)
        self.assertNotIn(Timestamp(1530711654, 0), rng)
        self.assertNotIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "_1530711653:999999999]")

    def test_bounded_on_right_exclusive(self):
        rng = TimeRange.from_end(Timestamp(1530711653, 999999999), TimeRange.EXCLUSIVE)

        self.assertIn(Timestamp(), rng)
        self.assertIn(Timestamp(326246400, 0), rng)
        self.assertIn(Timestamp(417799799, 999999999), rng)
        self.assertIn(Timestamp(417799800, 0), rng)
        self.assertIn(Timestamp(1530711653, 0), rng)
        self.assertIn(Timestamp(1530711653, 999999998), rng)
        self.assertNotIn(Timestamp(1530711653, 999999999), rng)
        self.assertNotIn(Timestamp(1530711654, 0), rng)
        self.assertNotIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "_1530711653:999999999)")

    def test_bounded_on_left_inclusive(self):
        rng = TimeRange.from_start(Timestamp(417799799, 999999999))

        self.assertNotIn(Timestamp(), rng)
        self.assertNotIn(Timestamp(326246400, 0), rng)
        self.assertNotIn(Timestamp(417799799, 999999998), rng)
        self.assertIn(Timestamp(417799799, 999999999), rng)
        self.assertIn(Timestamp(417799800, 0), rng)
        self.assertIn(Timestamp(1530711653, 0), rng)
        self.assertIn(Timestamp(1530711653, 999999998), rng)
        self.assertIn(Timestamp(1530711653, 999999999), rng)
        self.assertIn(Timestamp(1530711654, 0), rng)
        self.assertIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "[417799799:999999999_")

    def test_bounded_on_left_exclusive(self):
        rng = TimeRange.from_start(Timestamp(417799799, 999999999), TimeRange.EXCLUSIVE)

        self.assertNotIn(Timestamp(), rng)
        self.assertNotIn(Timestamp(326246400, 0), rng)
        self.assertNotIn(Timestamp(417799799, 999999998), rng)
        self.assertNotIn(Timestamp(417799799, 999999999), rng)
        self.assertIn(Timestamp(417799800, 0), rng)
        self.assertIn(Timestamp(1530711653, 0), rng)
        self.assertIn(Timestamp(1530711653, 999999998), rng)
        self.assertIn(Timestamp(1530711653, 999999999), rng)
        self.assertIn(Timestamp(1530711654, 0), rng)
        self.assertIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "(417799799:999999999_")

    def test_bounded_inclusive(self):
        rng = TimeRange(Timestamp(417799799, 999999999), Timestamp(1530711653, 999999999))

        self.assertNotIn(Timestamp(), rng)
        self.assertNotIn(Timestamp(326246400, 0), rng)
        self.assertNotIn(Timestamp(417799799, 999999998), rng)
        self.assertIn(Timestamp(417799799, 999999999), rng)
        self.assertIn(Timestamp(417799800, 0), rng)
        self.assertIn(Timestamp(1530711653, 0), rng)
        self.assertIn(Timestamp(1530711653, 999999998), rng)
        self.assertIn(Timestamp(1530711653, 999999999), rng)
        self.assertNotIn(Timestamp(1530711654, 0), rng)
        self.assertNotIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "[417799799:999999999_1530711653:999999999]")

    def test_bounded_exclusive(self):
        rng = TimeRange(Timestamp(417799799, 999999999), Timestamp(1530711653, 999999999), TimeRange.EXCLUSIVE)

        self.assertNotIn(Timestamp(), rng)
        self.assertNotIn(Timestamp(326246400, 0), rng)
        self.assertNotIn(Timestamp(417799799, 999999998), rng)
        self.assertNotIn(Timestamp(417799799, 999999999), rng)
        self.assertIn(Timestamp(417799800, 0), rng)
        self.assertIn(Timestamp(1530711653, 0), rng)
        self.assertIn(Timestamp(1530711653, 999999998), rng)
        self.assertNotIn(Timestamp(1530711653, 999999999), rng)
        self.assertNotIn(Timestamp(1530711654, 0), rng)
        self.assertNotIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "(417799799:999999999_1530711653:999999999)")

    def test_single_ts(self):
        rng = TimeRange.from_single_timestamp(Timestamp(1530711653, 999999999))

        self.assertNotIn(Timestamp(), rng)
        self.assertNotIn(Timestamp(326246400, 0), rng)
        self.assertNotIn(Timestamp(417799799, 999999998), rng)
        self.assertNotIn(Timestamp(417799799, 999999999), rng)
        self.assertNotIn(Timestamp(417799800, 0), rng)
        self.assertNotIn(Timestamp(1530711653, 0), rng)
        self.assertNotIn(Timestamp(1530711653, 999999998), rng)
        self.assertIn(Timestamp(1530711653, 999999999), rng)
        self.assertNotIn(Timestamp(1530711654, 0), rng)
        self.assertNotIn(Timestamp(49391596800, 999999), rng)

        self.assertEqual(rng.to_sec_nsec_range(), "[1530711653:999999999]")

    def test_from_str(self):
        tests = [
            ("()", TimeRange.never()),
            ("[]", TimeRange.never()),
            ("", TimeRange.never()),
            ("_", TimeRange.eternity()),
            ("_1530711653:999999999", TimeRange.from_end(Timestamp(1530711653, 999999999))),
            ("[_1530711653:999999999]", TimeRange.from_end(Timestamp(1530711653, 999999999), TimeRange.INCLUSIVE)),
            ("(_1530711653:999999999)", TimeRange.from_end(Timestamp(1530711653, 999999999), TimeRange.EXCLUSIVE)),
            ("417799799:999999999_", TimeRange.from_start(Timestamp(417799799, 999999999))),
            ("[417799799:999999999_]", TimeRange.from_start(Timestamp(417799799, 999999999), TimeRange.INCLUSIVE)),
            ("(417799799:999999999_)", TimeRange.from_start(Timestamp(417799799, 999999999), TimeRange.EXCLUSIVE)),
            ("417799799:999999999_1530711653:999999999", TimeRange(Timestamp(417799799, 999999999),
                                                                   Timestamp(1530711653, 999999999))),
            ("[417799799:999999999_1530711653:999999999]", TimeRange(Timestamp(417799799, 999999999),
                                                                     Timestamp(1530711653, 999999999),
                                                                     TimeRange.INCLUSIVE)),
            ("(417799799:999999999_1530711653:999999999)", TimeRange(Timestamp(417799799, 999999999),
                                                                     Timestamp(1530711653, 999999999),
                                                                     TimeRange.EXCLUSIVE)),
            ("(417799799:999999999_1530711653:999999999]", TimeRange(Timestamp(417799799, 999999999),
                                                                     Timestamp(1530711653, 999999999),
                                                                     TimeRange.INCLUDE_END)),
            ("[417799799:999999999_1530711653:999999999)", TimeRange(Timestamp(417799799, 999999999),
                                                                     Timestamp(1530711653, 999999999),
                                                                     TimeRange.INCLUDE_START)),
            ("1530711653:999999999", TimeRange.from_single_timestamp(Timestamp(1530711653, 999999999))),
        ]

        for (s, tr) in tests:
            self.assertEqual(tr, TimeRange.from_str(s))

    def test_subrange(self):
        a = Timestamp(326246400, 0)
        b = Timestamp(417799799, 999999999)
        c = Timestamp(1530711653, 999999999)
        d = Timestamp(49391596800, 999999)

        self.assertTrue(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(TimeRange(a, b, TimeRange.INCLUSIVE)))
        self.assertFalse(TimeRange(a, c, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(a, b, TimeRange.INCLUSIVE)))
        self.assertTrue(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(TimeRange(a, b, TimeRange.EXCLUSIVE)))
        self.assertTrue(TimeRange(a, c, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(a, b, TimeRange.EXCLUSIVE)))

        self.assertTrue(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.INCLUSIVE)))
        self.assertFalse(TimeRange(a, c, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.INCLUSIVE)))
        self.assertTrue(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.EXCLUSIVE)))
        self.assertTrue(TimeRange(a, c, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.EXCLUSIVE)))

        self.assertTrue(TimeRange(a, d, TimeRange.INCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.INCLUSIVE)))
        self.assertTrue(TimeRange(a, d, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.INCLUSIVE)))
        self.assertTrue(TimeRange(a, d, TimeRange.INCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.EXCLUSIVE)))
        self.assertTrue(TimeRange(a, d, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(b, c, TimeRange.EXCLUSIVE)))

        self.assertFalse(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(TimeRange(b, d, TimeRange.INCLUSIVE)))
        self.assertFalse(TimeRange(a, c, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(b, d, TimeRange.INCLUSIVE)))
        self.assertFalse(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(TimeRange(b, d, TimeRange.EXCLUSIVE)))
        self.assertFalse(TimeRange(a, c, TimeRange.EXCLUSIVE).contains_subrange(TimeRange(b, d, TimeRange.EXCLUSIVE)))

    def test_intersection(self):
        a = Timestamp(326246400, 0)
        b = Timestamp(417799799, 999999999)
        c = Timestamp(1530711653, 999999999)
        d = Timestamp(49391596800, 999999)

        self.assertEqual(TimeRange(a, b, TimeRange.INCLUSIVE).intersect_with(TimeRange(c, d, TimeRange.INCLUSIVE)),
                         TimeRange.never())

        self.assertEqual(TimeRange(a, b, TimeRange.INCLUSIVE).intersect_with(TimeRange(b, c, TimeRange.INCLUSIVE)),
                         TimeRange.from_single_timestamp(b))

        self.assertEqual(TimeRange(a, b, TimeRange.EXCLUSIVE).intersect_with(TimeRange(b, c, TimeRange.INCLUSIVE)),
                         TimeRange.never())

        self.assertEqual(TimeRange(a, c, TimeRange.INCLUSIVE).intersect_with(TimeRange(b, d, TimeRange.INCLUSIVE)),
                         TimeRange(b, c, TimeRange.INCLUSIVE))

        self.assertEqual(TimeRange(a, c, TimeRange.EXCLUSIVE).intersect_with(TimeRange(b, d, TimeRange.INCLUSIVE)),
                         TimeRange(b, c, TimeRange.INCLUDE_START))

        self.assertEqual(TimeRange(a, c, TimeRange.INCLUSIVE).intersect_with(TimeRange(b, d, TimeRange.EXCLUSIVE)),
                         TimeRange(b, c, TimeRange.INCLUDE_END))

        self.assertEqual(TimeRange(a, c, TimeRange.EXCLUSIVE).intersect_with(TimeRange(b, d, TimeRange.EXCLUSIVE)),
                         TimeRange(b, c, TimeRange.EXCLUSIVE))

        self.assertEqual(TimeRange(a, d, TimeRange.INCLUSIVE).intersect_with(TimeRange(b, c, TimeRange.INCLUSIVE)),
                         TimeRange(b, c, TimeRange.INCLUSIVE))

        self.assertEqual(TimeRange(a, d, TimeRange.EXCLUSIVE).intersect_with(TimeRange(b, c, TimeRange.INCLUSIVE)),
                         TimeRange(b, c, TimeRange.INCLUSIVE))

        self.assertEqual(TimeRange(a, d, TimeRange.INCLUSIVE).intersect_with(TimeRange(b, c, TimeRange.EXCLUSIVE)),
                         TimeRange(b, c, TimeRange.EXCLUSIVE))

        self.assertEqual(TimeRange(a, d, TimeRange.EXCLUSIVE).intersect_with(TimeRange(b, c, TimeRange.EXCLUSIVE)),
                         TimeRange(b, c, TimeRange.EXCLUSIVE))

        self.assertEqual(TimeRange.eternity().intersect_with(TimeRange(a, b, TimeRange.INCLUSIVE)),
                         TimeRange(a, b, TimeRange.INCLUSIVE))

        self.assertEqual(TimeRange.eternity().intersect_with(TimeRange(a, b, TimeRange.EXCLUSIVE)),
                         TimeRange(a, b, TimeRange.EXCLUSIVE))

        self.assertEqual(TimeRange.never().intersect_with(TimeRange(a, b, TimeRange.INCLUSIVE)),
                         TimeRange.never())

        self.assertEqual(TimeRange.never().intersect_with(TimeRange(a, b, TimeRange.EXCLUSIVE)),
                         TimeRange.never())

        self.assertEqual(TimeRange.never().intersect_with(TimeRange.eternity()),
                         TimeRange.never())

    def test_length(self):
        a = Timestamp(326246400, 0)
        b = Timestamp(417799799, 999999999)
        c = Timestamp(1530711653, 999999999)

        rng = TimeRange(a, b, TimeRange.INCLUSIVE)
        self.assertEqual(rng.length, b - a)

        rng = TimeRange(None, b, TimeRange.INCLUSIVE)
        self.assertEqual(rng.length, float("inf"))

        rng = TimeRange(a, None, TimeRange.INCLUSIVE)
        self.assertEqual(rng.length, float("inf"))

        rng = TimeRange(None, None, TimeRange.INCLUSIVE)
        self.assertEqual(rng.length, float("inf"))

        rng = TimeRange(a, b, TimeRange.INCLUSIVE)
        with self.assertRaises(TsValueError):
            rng.length = (c - a)
        self.assertEqual(rng, TimeRange(a, b, TimeRange.INCLUSIVE))

        rng = TimeRange(None, None, TimeRange.INCLUSIVE)
        with self.assertRaises(TsValueError):
            rng.length = (b - a)

        rng = TimeRange(a, b, TimeRange.INCLUSIVE)
        with self.assertRaises(TsValueError):
            rng.length = (a - c)

    def test_repr(self):
        """This tests that the repr function turns time ranges into `eval`-able strings."""
        test_trs = [
            (TimeRange.from_str("(10:1_10:2)"), "mediatimestamp.immutable.TimeRange.from_str('(10:1_10:2)')"),
            (TimeRange.from_str("[1:0_10:0]"), "mediatimestamp.immutable.TimeRange.from_str('[1:0_10:0]')"),
            (TimeRange.from_str("[10:0_"), "mediatimestamp.immutable.TimeRange.from_str('[10:0_')")
        ]

        for t in test_trs:
            self.assertEqual(repr(t[0]), t[1])

    def test_at_rate(self):
        test_data = [
            (TimeRange.from_str("[10:0_11:0)"), 50, TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]),
            (TimeRange.from_str("[10:0_11:0)"), 50, TimeOffset(0, 100),
             [Timestamp(10, 100) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]),
            (TimeRange.from_str("[10:0_11:0]"), 50, TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 50, 1) for n in range(0, 51)]),
            (TimeRange.from_str("[10:0_11:0]"), 50, TimeOffset(0, 100),
             [Timestamp(10, 100) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]),
            (TimeRange.from_str("(10:0_11:0)"), 50, TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 50, 1) for n in range(1, 50)]),
            (TimeRange.from_str("(10:0_11:0)"), 50, TimeOffset(0, 100),
             [Timestamp(10, 100) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]),
            (TimeRange.from_str("(10:0_11:0]"), 50, TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 50, 1) for n in range(1, 51)]),
            (TimeRange.from_str("(10:0_11:0]"), 50, TimeOffset(0, 100),
             [Timestamp(10, 100) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]),
        ]

        for (tr, rate, phase_offset, expected) in test_data:
            self.assertEqual(list(tr.at_rate(rate, phase_offset=phase_offset)), expected)
            self.assertEqual(list(tr.reversed_at_rate(rate, phase_offset=phase_offset)), list(reversed(expected)))

        gen = TimeRange.from_str("[10:0_").at_rate(50)
        for ts in [Timestamp(10, 0) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]:
            self.assertEqual(next(gen), ts)

        gen = TimeRange.from_str("_10:0]").reversed_at_rate(50)
        for ts in [Timestamp(10, 0) - TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]:
            self.assertEqual(next(gen), ts)

        self.assertEqual(list(TimeRange.from_str("[10:0_10:50)")),
                         [Timestamp(10, 0) + TimeOffset(0, n) for n in range(0, 50)])
        self.assertEqual(list(reversed(TimeRange.from_str("[10:0_10:50)"))),
                         [Timestamp(10, 0) + TimeOffset(0, 49 - n) for n in range(0, 50)])

    def test_comparisons(self):
        # Test data format:
        #  (a, b,
        #   (starts_inside, ends_inside, is_earlier, is_later,
        #    starts_earlier, starts_later, ends_earlier, ends_later,
        #    overlaps_with, is_contiguous_with))
        test_data = [
            (TimeRange.from_str("_"), TimeRange.from_str("_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeRange.from_str("_"), TimeRange.from_str("[0:0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeRange.from_str("_"), TimeRange.from_str("_0:0]"),
             (True, False, False, False, False, False, False, True, True, True)),
            (TimeRange.from_str("_"), TimeRange.from_str("[0:0_10:0)"),
             (False, False, False, False, True, False, False, True, True, True)),

            (TimeRange.from_str("_5:0)"), TimeRange.from_str("_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("_5:0)"), TimeRange.from_str("[0:0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeRange.from_str("_5:0)"), TimeRange.from_str("_0:0]"),
             (True, False, False, False, False, False, False, True, True, True)),
            (TimeRange.from_str("_5:0)"), TimeRange.from_str("_10:0]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("_5:0)"), TimeRange.from_str("[0:0_10:0)"),
             (False, True, False, False, True, False, True, False, True, True)),

            (TimeRange.from_str("_0:0)"), TimeRange.from_str("_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("[0:0_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("_0:0]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("_0:0)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("_10:0]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("[0:0_10:0)"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("(0:0_10:0)"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("[5:0_10:0)"),
             (False, False, True, False, True, False, True, False, False, False)),

            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("[0:0_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("(0:0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("[5:0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("_0:0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("_0:0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("_10:0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("[0:0_10:0)"),
             (True, False, False, False, False, False, False, True, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("(0:0_10:0)"),
             (False, False, False, False, True, False, False, True, True, True)),
            (TimeRange.from_str("[0:0_)"), TimeRange.from_str("[5:0_10:0)"),
             (False, False, False, False, True, False, False, True, True, True)),

            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("[0:0_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("(0:0_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("[5:0_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("(5:0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("_0:0]"),
             (False, False, False, True, False, True, False, True, False, False)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("_0:0)"),
             (False, False, False, True, False, True, False, True, False, False)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("_10:0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("[0:0_10:0)"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("(0:0_10:0)"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[5:0_)"), TimeRange.from_str("[5:0_10:0)"),
             (True, False, False, False, False, False, False, True, True, True)),

            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[0:0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("(0:0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[10:0_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("(10:0_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("_0:0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("_0:0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("_10:0]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("_10:0)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[0:0_10:0)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("(0:0_10:0)"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[5:0_10:0)"),
             (False, True, False, False, True, False, False, False, True, True)),

            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("[0:0_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("(0:0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("[10:0_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("(10:0_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("_0:0]"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("_0:0)"),
             (False, False, False, True, False, True, False, True, False, False)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("_10:0]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("_10:0)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("[0:0_10:0)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("(0:0_10:0)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeRange.from_str("(0:0_10:0)"), TimeRange.from_str("[5:0_10:0)"),
             (False, True, False, False, True, False, False, False, True, True)),

            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[0:0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("(0:0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[10:0_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("(10:0_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("_0:0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("_0:0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("_10:0]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("_10:0)"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[0:0_10:0)"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("(0:0_10:0)"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[5:0_10:0)"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("(5:0_10:0)"),
             (False, False, True, False, True, False, True, False, False, False)),

            (TimeRange.never(), TimeRange.from_str("_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("[0:0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("(0:0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("[10:0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("(10:0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("_0:0]"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("_0:0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("_10:0]"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("_10:0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("[0:0_10:0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("(0:0_10:0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("[5:0_10:0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeRange.never(), TimeRange.from_str("(5:0_10:0)"),
             (False, False, False, False, False, False, False, False, True, True)),
        ]
        functions = ("starts_inside_timerange",
                     "ends_inside_timerange",
                     "is_earlier_than_timerange",
                     "is_later_than_timerange",
                     "starts_earlier_than_timerange",
                     "starts_later_than_timerange",
                     "ends_earlier_than_timerange",
                     "ends_later_than_timerange",
                     "overlaps_with_timerange",
                     "is_contiguous_with_timerange")

        for (a, b, expected) in test_data:
            for (fname, expected_value) in zip(functions, expected):
                with self.subTest(a=a, b=b, fname=fname, expected_value=expected_value):
                    if expected_value:
                        self.assertTrue(getattr(a, fname)(b),
                                        msg="{!r}.{}({!r}) is False, expected to be True".format(a, fname, b))
                    else:
                        self.assertFalse(getattr(a, fname)(b),
                                         msg="{!r}.{}({!r}) is True, expected to be False".format(a, fname, b))

    def test_split(self):
        test_data = [
            (TimeRange.from_str("_"), Timestamp.from_str("0:0"),
             TimeRange.from_str("_0:0)"), TimeRange.from_str("[0:0_")),
            (TimeRange.from_str("[0:0_"), Timestamp.from_str("10:0"),
             TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[10:0_")),
            (TimeRange.from_str("_10:0)"), Timestamp.from_str("0:0"),
             TimeRange.from_str("_0:0)"), TimeRange.from_str("[0:0_10:0)")),
            (TimeRange.from_str("[0:0_10:0)"), Timestamp.from_str("5:0"),
             TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[5:0_10:0)")),
            (TimeRange.from_str("[0:0_10:0]"), Timestamp.from_str("5:0"),
             TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[5:0_10:0]")),
            (TimeRange.from_str("(0:0_10:0)"), Timestamp.from_str("5:0"),
             TimeRange.from_str("(0:0_5:0)"), TimeRange.from_str("[5:0_10:0)")),
            (TimeRange.from_str("(0:0_10:0]"), Timestamp.from_str("5:0"),
             TimeRange.from_str("(0:0_5:0)"), TimeRange.from_str("[5:0_10:0]")),
            (TimeRange.from_str("[0:0]"), Timestamp.from_str("0:0"),
             TimeRange.never(), TimeRange.from_str("[0:0_0:0]")),
            (TimeRange.from_str("[0:0_10:0)"), Timestamp.from_str("0:0"),
             TimeRange.never(), TimeRange.from_str("[0:0_10:0)")),
            (TimeRange.from_str("[0:0_10:0]"), Timestamp.from_str("10:0"),
             TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[10:0]")),
        ]

        for (tr, ts, left, right) in test_data:
            with self.subTest(tr=tr, ts=ts, expected=(left, right)):
                self.assertEqual(tr.split_at(ts), (left, right))

        test_data = [
            (TimeRange.from_str("[0:0_10:0)"), Timestamp.from_str("11:0")),
            (TimeRange.from_str("[0:0_10:0)"), Timestamp.from_str("10:0")),
            (TimeRange.from_str("[0:0_10:0]"), Timestamp.from_str("10:1")),
        ]

        for (tr, ts) in test_data:
            with self.subTest(tr=tr, ts=ts):
                with self.assertRaises(ValueError):
                    tr.split_at(ts)

    def test_timerange_between(self):
        test_data = [
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[5:0_15:0)"),
                TimeRange.never()),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[15:0_20:0)"),
                TimeRange.from_str("[10:0_15:0)")),
            (TimeRange.from_str("[0:0_10:0]"), TimeRange.from_str("(15:0_20:0)"),
                TimeRange.from_str("(10:0_15:0]")),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[15:0_20:0)"),
                TimeRange.from_str("[10:0_15:0)")),
            (TimeRange.from_str("[0:0_10:0]"), TimeRange.from_str("(15:0_20:0)"),
                TimeRange.from_str("(10:0_15:0]")),
        ]

        for (left, right, expected) in test_data:
            with self.subTest(left=left, right=right, expected=expected):
                self.assertEqual(left.timerange_between(right), expected)
                self.assertEqual(right.timerange_between(left), expected)

    def test_normalise(self):
        tests_tr = [
            (TimeRange.from_str("[0:0_1:0)"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:0_1:0)")),
            (TimeRange.from_str("[0:0_1:0]"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:0_1:40000000)")),
            (TimeRange.from_str("(0:0_1:0)"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:40000000_1:0)")),
            (TimeRange.from_str("(0:0_1:0]"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:40000000_1:40000000)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:0_1:0)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_DOWN,
             TimeRange.from_str("[0:0_0:960000000)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_UP,
             TimeRange.from_str("[0:40000000_1:0)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_IN,
             TimeRange.from_str("[0:40000000_0:960000000)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_OUT,
             TimeRange.from_str("[0:0_1:0)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_START,
             TimeRange.from_str("[0:0_0:960000000)")),
            (TimeRange.from_str("[0:10000000_0:999999999)"), Fraction(25, 1), TimeRange.ROUND_END,
             TimeRange.from_str("[0:40000000_1:0)")),
            (TimeRange.from_str("(0:10000000_0:999999999]"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:40000000_1:40000000)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:40000000_1:0)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_UP,
             TimeRange.from_str("[0:40000000_1:40000000)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_DOWN,
             TimeRange.from_str("[0:0_1:0)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_IN,
             TimeRange.from_str("[0:40000000_1:0)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_OUT,
             TimeRange.from_str("[0:0_1:40000000)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_START,
             TimeRange.from_str("[0:40000000_1:40000000)")),
            (TimeRange.from_str("[0:39999999_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_END,
             TimeRange.from_str("[0:0_1:0)")),
            (TimeRange.from_str("[0:39999999_"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("[0:40000000_")),
            (TimeRange.from_str("_1:10000000)"), Fraction(25, 1), TimeRange.ROUND_NEAREST,
             TimeRange.from_str("_1:0)")),
        ]

        for (tr, rate, rounding, expected) in tests_tr:
            with self.subTest(tr=tr, rate=rate, expected=expected):
                result = tr.normalise(rate.numerator, rate.denominator, rounding=rounding)
                self.assertEqual(result, expected,
                                 msg=("{!r}.normalise({}, {}, rounding={}) == {!r}, expected {!r}"
                                      .format(tr, rate.numerator, rate.denominator, rounding, result, expected)))

    def test_extend_to_encompass(self):
        test_data = [
            (TimeRange.from_str("()"), TimeRange.from_str("()"),
             TimeRange.from_str("()")),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[10:0]"),
             TimeRange.from_str("[0:0_10:0]")),
            (TimeRange.from_str("_"), TimeRange.from_str("[0:0]"),
             TimeRange.from_str("_")),
            (TimeRange.from_str("_"), TimeRange.from_str("()"),
             TimeRange.from_str("_")),
            (TimeRange.from_str("()"), TimeRange.from_str("_"),
             TimeRange.from_str("_")),
            (TimeRange.from_str("_10:0)"), TimeRange.from_str("[0:0_"),
             TimeRange.from_str("_")),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[5:0_"),
             TimeRange.from_str("[0:0_")),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[5:0_15:0)"),
             TimeRange.from_str("[0:0_15:0)")),
            (TimeRange.from_str("[0:0_10:0)"), TimeRange.from_str("[10:0_15:0)"),
             TimeRange.from_str("[0:0_15:0)")),
            (TimeRange.from_str("()"), TimeRange.from_str("[5:0_"),
             TimeRange.from_str("[5:0_")),
            (TimeRange.from_str("()"), TimeRange.from_str("[5:0_15:0)"),
             TimeRange.from_str("[5:0_15:0)")),
            (TimeRange.from_str("()"), TimeRange.from_str("_15:0)"),
             TimeRange.from_str("_15:0)")),

            # discontiguous
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("(0:0_"),
             TimeRange.from_str("_")),
            (TimeRange.from_str("(0:0_"), TimeRange.from_str("_0:0)"),
             TimeRange.from_str("_")),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("(5:0_15:0)"),
             TimeRange.from_str("[0:0_15:0)")),
            (TimeRange.from_str("(5:0_15:0)"), TimeRange.from_str("[0:0_5:0)"),
             TimeRange.from_str("[0:0_15:0)")),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[10:0_15:0)"),
             TimeRange.from_str("[0:0_15:0)")),
            (TimeRange.from_str("[10:0_15:0)"), TimeRange.from_str("[0:0_5:0)"),
             TimeRange.from_str("[0:0_15:0)")),
        ]

        for (first, second, expected) in test_data:
            with self.subTest(first=first, second=second, expected=expected):
                self.assertEqual(first.extend_to_encompass_timerange(second), expected)

    def test_union_raises(self):
        # discontiguous part of test_extend_to_encompass raises for a union
        test_data = [
            (TimeRange.from_str("_0:0)"), TimeRange.from_str("(0:0_")),
            (TimeRange.from_str("(0:0_"), TimeRange.from_str("_0:0)")),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("(5:0_15:0)")),
            (TimeRange.from_str("(5:0_15:0)"), TimeRange.from_str("[0:0_5:0)")),
            (TimeRange.from_str("[0:0_5:0)"), TimeRange.from_str("[10:0_15:0)")),
            (TimeRange.from_str("[10:0_15:0)"), TimeRange.from_str("[0:0_5:0)")),
        ]

        for (first, second) in test_data:
            with self.subTest(first=first, second=second):
                with self.assertRaises(ValueError):
                    first.union_with_timerange(second)
