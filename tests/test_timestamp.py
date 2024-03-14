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
from unittest import mock
from datetime import datetime
from dateutil import tz
from fractions import Fraction
from copy import deepcopy

from mediatimestamp.immutable import (
    Timestamp,
    TsValueError,
    mediatimestamp,
    SupportsMediaTimestamp)


class TestTimestamp(unittest.TestCase):
    def test_mediatimestamp(self):
        ts = Timestamp()
        self.assertIsInstance(ts, SupportsMediaTimestamp)

        self.assertEqual(ts, mediatimestamp(ts))

        class _convertable (object):
            def __mediatimestamp__(self) -> Timestamp:
                return Timestamp()

        c = _convertable()
        self.assertIsInstance(c, SupportsMediaTimestamp)

        self.assertEqual(ts, mediatimestamp(c))

    def test_MAX_NANOSEC(self):
        self.assertEqual(Timestamp.MAX_NANOSEC, 1000000000)

    def test_normalise(self):
        tests_ts = [
            (Timestamp(0, 0), Fraction(30000, 1001), Timestamp.ROUND_NEAREST,
             Timestamp(0, 0)),
            (Timestamp(1001, 0), Fraction(30000, 1001), Timestamp.ROUND_NEAREST,
             Timestamp(1001, 0)),
            (Timestamp(1001, 1001.0/30000/2*1000000000), Fraction(30000, 1001), Timestamp.ROUND_NEAREST,
             Timestamp(1001, 0)),
            (Timestamp(1001, 1001.0/30000/2*1000000000 + 1), Fraction(30000, 1001), Timestamp.ROUND_NEAREST,
             Timestamp(1001, 1001.0/30000*1000000000)),
            (Timestamp(1001, 1001.0/30000/2*1000000000, -1), Fraction(30000, 1001), Timestamp.ROUND_NEAREST,
             Timestamp(1001, 0, -1)),
            (Timestamp(1001, 1001.0/30000/2*1000000000 + 1, -1), Fraction(30000, 1001), Timestamp.ROUND_NEAREST,
             Timestamp(1001, 1001.0/30000*1000000000, -1)),
            (Timestamp(1521731233, 320000000), Fraction(25, 3), Timestamp.ROUND_NEAREST,
             Timestamp(1521731233, 320000000)),
            (Timestamp(0, 0), Fraction(30000, 1001), Timestamp.ROUND_UP,
             Timestamp(0, 0)),
            (Timestamp(1001, 0), Fraction(30000, 1001), Timestamp.ROUND_UP,
             Timestamp(1001, 0)),
            (Timestamp(1001, 1001.0/30000/2*1000000000), Fraction(30000, 1001), Timestamp.ROUND_UP,
             Timestamp(1001, 1001.0/30000*1000000000)),
            (Timestamp(1001, 1001.0/30000/2*1000000000 + 1), Fraction(30000, 1001), Timestamp.ROUND_UP,
             Timestamp(1001, 1001.0/30000*1000000000)),
            (Timestamp(1001, 1001.0/30000/2*1000000000, -1), Fraction(30000, 1001), Timestamp.ROUND_UP,
             Timestamp(1001, 0, -1)),
            (Timestamp(1001, 1001.0/30000/2*1000000000 + 1, -1), Fraction(30000, 1001), Timestamp.ROUND_UP,
             Timestamp(1001, 0, -1)),
            (Timestamp(1521731233, 320000000), Fraction(25, 3), Timestamp.ROUND_UP,
             Timestamp(1521731233, 320000000)),
            (Timestamp(0, 0), Fraction(30000, 1001), Timestamp.ROUND_DOWN,
             Timestamp(0, 0)),
            (Timestamp(1001, 0), Fraction(30000, 1001), Timestamp.ROUND_DOWN,
             Timestamp(1001, 0)),
            (Timestamp(1001, 1001.0/30000/2*1000000000), Fraction(30000, 1001), Timestamp.ROUND_DOWN,
             Timestamp(1001, 0)),
            (Timestamp(1001, 1001.0/30000/2*1000000000 + 1), Fraction(30000, 1001), Timestamp.ROUND_DOWN,
             Timestamp(1001, 0)),
            (Timestamp(1001, 1001.0/30000/2*1000000000, -1), Fraction(30000, 1001), Timestamp.ROUND_DOWN,
             Timestamp(1001, 1001.0/30000*1000000000, -1)),
            (Timestamp(1001, 1001.0/30000/2*1000000000 + 1, -1), Fraction(30000, 1001), Timestamp.ROUND_DOWN,
             Timestamp(1001, 1001.0/30000*1000000000, -1)),
            (Timestamp(1521731233, 320000000), Fraction(25, 3), Timestamp.ROUND_DOWN,
             Timestamp(1521731233, 320000000)),
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
        self.assertEqual(hash(Timestamp(0, 0)), hash(Timestamp(0, 0)))
        self.assertNotEqual(hash(Timestamp(0, 0)), hash(Timestamp(0, 1)))

    def test_subsec(self):
        """This tests that Timestamps can be converted to millisec, nanosec, and microsec values."""
        tests_ts = [
            (Timestamp(1, 1000000), "to_millisec", (), 1001),
            (Timestamp(1, 1000), "to_microsec", (), 1000001),
            (Timestamp(1, 1), "to_nanosec", (), 1000000001),
            (Timestamp, 'from_millisec', (1001,), Timestamp(1, 1000000)),
            (Timestamp, 'from_microsec', (1000001,), Timestamp(1, 1000)),
            (Timestamp, 'from_nanosec', (1000000001,), Timestamp(1, 1)),
            (Timestamp(1, 500000), 'to_millisec', (Timestamp.ROUND_DOWN,), 1000),
            (Timestamp(1, 500000), 'to_millisec', (Timestamp.ROUND_NEAREST,), 1001),
            (Timestamp(1, 499999), 'to_millisec', (Timestamp.ROUND_NEAREST,), 1000),
            (Timestamp(1, 500000), 'to_millisec', (Timestamp.ROUND_UP,), 1001),
            (Timestamp(1, 500000, -1), 'to_millisec', (Timestamp.ROUND_DOWN,), -1001),
            (Timestamp(1, 500000, -1), 'to_millisec', (Timestamp.ROUND_NEAREST,), -1001),
            (Timestamp(1, 499999, -1), 'to_millisec', (Timestamp.ROUND_NEAREST,), -1000),
            (Timestamp(1, 500000, -1), 'to_millisec', (Timestamp.ROUND_UP,), -1000)
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = getattr(t[0], t[1])(*t[2])
                self.assertEqual(r, t[3],
                                 msg="{!r}.{}{!r} == {!r}, expected {!r}".format(t[0], t[1], t[2], r, t[3]))

    def test_interval_frac(self):
        """This tests that Timestamps can be converted to interval fractions."""
        tests_ts = [
            ((50, 1, 1), Timestamp(0, 20000000)),
            ((50, 1, 2), Timestamp(0, 10000000))
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = Timestamp.get_interval_fraction(*t[0])
                self.assertEqual(r, t[1],
                                 msg=("Timestamp.get_interval_fraction{!r} == {!r}, expected {!r}"
                                      .format(t[0], r, t[1])))

        bad_params = [(0, 1, 1),
                      (50, 0, 1),
                      (50, 1, 0)]

        for params in bad_params:
            with self.assertRaises(TsValueError,
                                   msg=("Timestamp.get_interval_fraction{!r} should have raised TsValueError exception"
                                        .format(params))):
                Timestamp.get_interval_fraction(*params)

    def test_from_sec_frac(self):
        """This tests that timestamps can be instantiated from fractional second values."""
        tests_ts = [
            (("1.000000001",), Timestamp(1, 1)),
            (("-1.000000001",), Timestamp(1, 1, sign=-1)),
            (("1.000001POTATO",), Timestamp(1, 1000)),
            (("1",), Timestamp(1, 0)),
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = Timestamp.from_sec_frac(*t[0])
                self.assertEqual(r, t[1],
                                 msg="Timestamp.from_sec_frac{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

        bad_params = [("0.0.1",), ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_sec_frac(*params)

    def test_from_sec_nsec(self):
        """This tests that timestamps can be created from second:nanosecond pairs."""
        tests_ts = [
            (("1:1",), Timestamp(1, 1)),
            (("-1:1",), Timestamp(1, 1, sign=-1)),
            (("1",), Timestamp(1, 0)),
        ]

        for t in tests_ts:
            with self.subTest(t=t):
                r = Timestamp.from_sec_nsec(*t[0])
                self.assertEqual(r, t[1],
                                 msg="Timestamp.from_sec_nsec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

        bad_params = [("0:0:1",), ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_sec_nsec(*params)

    def test_from_count(self):
        """This tests that timestamps can be created from counts at a specified frequency."""
        tests_ts = [
            ((1, 50, 1), Timestamp(0, 20000000)),
            ((75, 50, 1), Timestamp(1, 500000000)),
            ((-75, 50, 1), Timestamp(1, 500000000, -1))
        ]

        for t in tests_ts:
            r = Timestamp.from_count(*t[0])
            self.assertEqual(r, t[1],
                             msg="Timestamp.from_count{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

        bad_params = [(1, 0, 1),
                      (1, 1, 0)]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_count(*params)

    def test_from_millisec(self):
        """This tests that timestamps can be created from millisecond values."""
        tests_ts = [
            ((1,), Timestamp(0, 1000000)),
            ((1000,), Timestamp(1, 0)),
            ((-1,), Timestamp(0, 1000000, -1))
        ]

        for t in tests_ts:
            r = Timestamp.from_millisec(*t[0])
            self.assertEqual(r, t[1],
                             msg="Timestamp.from_millisec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_from_microsec(self):
        """This tests that timestamps can be created from microsecond values."""
        tests_ts = [
            ((1,), Timestamp(0, 1000)),
            ((1000000,), Timestamp(1, 0)),
            ((-1,), Timestamp(0, 1000, -1))
        ]

        for t in tests_ts:
            r = Timestamp.from_microsec(*t[0])
            self.assertEqual(r, t[1],
                             msg="Timestamp.from_microsec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_from_nanosec(self):
        """This tests that timestamps can be created from nanosecond values."""
        tests_ts = [
            ((1,), Timestamp(0, 1)),
            ((1000000000,), Timestamp(1, 0)),
            ((-1,), Timestamp(0, 1, -1))
        ]

        for t in tests_ts:
            r = Timestamp.from_nanosec(*t[0])
            self.assertEqual(r, t[1],
                             msg="Timestamp.from_nanosec{!r} == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_from_float(self):
        """This tests that timestamps can be created from a float."""
        cases = [
            ((float(1.0)), Timestamp(1, 0)),
            ((float(1_000_000_000)), Timestamp(1_000_000_000, 0)),
            ((float(2.76)), Timestamp(2, 760_000_000)),
            ((float(-3.14)), Timestamp(3, 140_000_000, -1)),
            ((float(0.02)), Timestamp(0, 20_000_000))
        ]

        for case in cases:
            with self.subTest(case=case):
                r = Timestamp.from_float(case[0])
                self.assertEqual(r, case[1],
                                 msg="Timestamp.from_float{!r} == {!r}, expected {!r}".format(case[0], r, case[1]))

    def test_to_float(self):
        """This tests that timestamps can be created from a float."""
        cases = [
            ((float(1.0)), Timestamp(1, 0)),
            ((float(1_000_000_000)), Timestamp(1_000_000_000, 0)),
            ((float(2.76)), Timestamp(2, 760_000_000)),
            ((float(-3.14)), Timestamp(3, 140_000_000, -1)),
            ((float(0.02)), Timestamp(0, 20_000_000))
        ]

        for case in cases:
            with self.subTest(case=case):
                r = case[1].to_float()
                self.assertEqual(r, case[1],
                                 msg="{!r},to_float() == {!r}, expected {!r}".format(case[1], r, case[0]))

    def test_set_value(self):
        """This tests that timestamps cannot have their value set."""
        tests_ts = [
            (Timestamp(0, 0), Timestamp(0, 1), (0, 1)),
            (Timestamp(0, 0), Timestamp(1, 0), (1, 0)),
            (Timestamp(0, 0), Timestamp(0, 1, -1), (0, 1, -1))
        ]

        for t in tests_ts:
            ts = deepcopy(t[0])
            with self.assertRaises(AttributeError):
                ts.set_value(*t[2])
            self.assertEqual(ts, t[0])

    def test_to_count(self):
        """This tests that timestamps can be converted to counts at particular frequencies."""
        tests_ts = [
            (Timestamp(0, 20000000), (50, 1), 1),
            (Timestamp(1, 500000000), (50, 1), 75),
            (Timestamp(1, 500000000, -1), (50, 1), -75),
            # below .5 frame
            (Timestamp(100, 29999999), (50, 1), 100 * 50 + 1),
            # at .5 frame
            (Timestamp(100, 30000000), (50, 1), 100 * 50 + 2),
            # above .5 frame
            (Timestamp(100, 30000001), (50, 1), 100 * 50 + 2),
            # below negative .5 frame
            (Timestamp(100, 9999999), (50, 1), 100 * 50),
            # at negative .5 frame
            (Timestamp(100, 10000000), (50, 1), 100 * 50 + 1),
            # above negative .5 frame
            (Timestamp(100, 10000001), (50, 1), 100 * 50 + 1),
            # below .5 frame, round up
            (Timestamp(100, 29999999), (50, 1, Timestamp.ROUND_UP), 100 * 50 + 2),
            # at .5 frame, round down
            (Timestamp(100, 30000000), (50, 1, Timestamp.ROUND_DOWN), 100 * 50 + 1),
            # above .5 frame, round down
            (Timestamp(100, 30000001), (50, 1, Timestamp.ROUND_DOWN), 100 * 50 + 1),
            # below .5 frame, round up
            (Timestamp(100, 29999999, -1), (50, 1, Timestamp.ROUND_DOWN), -100 * 50 - 2),
            # at .5 frame, round down
            (Timestamp(100, 30000000, -1), (50, 1, Timestamp.ROUND_UP), -100 * 50 - 1),
            # above .5 frame, round down
            (Timestamp(100, 30000001, -1), (50, 1, Timestamp.ROUND_UP), -100 * 50 - 1),
        ]

        for t in tests_ts:
            r = t[0].to_count(*t[1])
            self.assertEqual(r, t[2],
                             msg="{!r}.to_count{!r} == {!r}, expected {!r}".format(t[0], t[1], r, t[2]))

        bad_params = [(1, 0),
                      (0, 1)]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp(0, 0).to_count(*params)

    def test_to_microsec(self):
        """This tests that timestamps can be converted to microsecond values."""
        tests_ts = [
            (Timestamp(0, 1000), (), 1),
            (Timestamp(1, 1000000), (), 1001000),
            (Timestamp(1, 1000000, -1), (), -1001000),
            # below .5 us
            (Timestamp(100, 1499), (), 100 * 1000000 + 1),
            # at .5 us
            (Timestamp(100, 1500), (), 100 * 1000000 + 2),
            # above .5 us
            (Timestamp(100, 1501), (), 100 * 1000000 + 2),
            # below .5 us, round up
            (Timestamp(100, 1499), (Timestamp.ROUND_UP,), 100 * 1000000 + 2),
            # at .5 us, round up
            (Timestamp(100, 1500), (Timestamp.ROUND_UP,), 100 * 1000000 + 2),
            # above .5 us, round up
            (Timestamp(100, 1501), (Timestamp.ROUND_UP,), 100 * 1000000 + 2),
            # below .5 us, round down
            (Timestamp(100, 1499), (Timestamp.ROUND_DOWN,), 100 * 1000000 + 1),
            # at .5 us, round down
            (Timestamp(100, 1500), (Timestamp.ROUND_DOWN,), 100 * 1000000 + 1),
            # above .5 us, round down
            (Timestamp(100, 1501), (Timestamp.ROUND_DOWN,), 100 * 1000000 + 1),
            # below .5 us, round down
            (Timestamp(100, 1499, -1), (Timestamp.ROUND_DOWN,), -100 * 1000000 - 2),
            # at .5 us, round down
            (Timestamp(100, 1500, -1), (Timestamp.ROUND_DOWN,), -100 * 1000000 - 2),
            # above .5 us, round down
            (Timestamp(100, 1501, -1), (Timestamp.ROUND_DOWN,), -100 * 1000000 - 2),
            # below .5 us, round up
            (Timestamp(100, 1499, -1), (Timestamp.ROUND_UP,), -100 * 1000000 - 1),
            # at .5 us, round up
            (Timestamp(100, 1500, -1), (Timestamp.ROUND_UP,), -100 * 1000000 - 1),
            # above .5 us, round up
            (Timestamp(100, 1501, -1), (Timestamp.ROUND_UP,), -100 * 1000000 - 1),
        ]

        for t in tests_ts:
            r = t[0].to_microsec(*t[1])
            self.assertEqual(r, t[2],
                             msg="{!r}.to_microsec{!r} == {!r}, expected {!r}".format(t[0], t[1], r, t[2]))

    def test_abs(self):
        """This tests that negative timestamps can be converted to positive ones using abs."""
        tests_ts = [
            (Timestamp(10, 1), Timestamp(10, 1)),
            (Timestamp(10, 1, -1), Timestamp(10, 1))
        ]

        for t in tests_ts:
            r = abs(t[0])
            self.assertEqual(r, t[1],
                             msg="abs({!r}) == {!r}, expected {!r}".format(t[0], r, t[1]))

    def test_average(self):
        """This tests that timestamps can be averaged."""
        ts1 = Timestamp(11, 976)
        ts2 = Timestamp(21, 51)
        ts_avg = (ts1 * 49 + ts2) // 50
        avg = int((ts1.to_nanosec() * 49 + ts2.to_nanosec()) // 50)
        self.assertEqual(avg, ts_avg.to_nanosec())

    def test_cast(self):
        """This tests that addition and subtraction of Timestamps and integers or floats works as expected."""
        tests_ts = [
            (Timestamp(10, 1), '+',  1, Timestamp(11, 1)),
            (Timestamp(10, 1), '-', 1, Timestamp(9, 1)),
            (Timestamp(10, 1), '+', 1.5, Timestamp(11, 500000001)),
            (Timestamp(10, 1), '-', 1.5, Timestamp(8, 500000001)),
        ]

        for t in tests_ts:
            if t[1] == '+':
                r = t[0] + t[2]
            else:
                r = t[0] - t[2]
            self.assertEqual(r, t[3],
                             msg="{!r} {} {!r} == {!r}, expected {}".format(t[0], t[1], t[2], r, t[3]))

        self.assertEqual(Timestamp(8, 500000000), 8.5)
        self.assertGreater(Timestamp(8, 500000000), 8)
        self.assertLess(Timestamp(8, 500000000), 8.6)
        self.assertNotEqual(Timestamp(8, 500000000), 8.6)

    def test_eq(self):
        """Test some equality operations"""
        self.assertEqual(Timestamp(10, 1), Timestamp(10, 1))
        self.assertNotEqual(Timestamp(10, 1), Timestamp(-10, 1))
        self.assertNotEqual(Timestamp(0, 1), Timestamp(0, -1))
        self.assertNotEqual(Timestamp(0, 1), None)
        self.assertEqual(Timestamp(0, 500000000), 0.5)
        self.assertNotEqual(Timestamp(0, 1), "0:1")

    def test_str(self):
        """This tests that the str function turns timestamps into second:nanosecond pairs."""
        tests_ts = [
            (str(Timestamp(10, 1)), "10:1"),
            (str(Timestamp(10, 1, -1)), "-10:1"),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_get_time_pythonic(self):
        """This tests that the fallback pure python implementation of get_time works as expected."""
        test_ts = [
            (1512489451.0, Timestamp(1512489451 + 37, 0)),
            (1512489451.1, Timestamp(1512489451 + 37, 100000000))
            ]

        for t in test_ts:
            with mock.patch("time.time") as time:
                time.return_value = t[0]
                gottime = Timestamp.get_time()
                self.assertEqual(gottime, t[1], msg="Times not equal, expected: %r, got %r" % (t[1], gottime))

    def test_iaddsub(self):
        """This tests integer addition and subtraction on timestamps."""
        ts = Timestamp(10, 0)
        ts += Timestamp(1, 2)
        self.assertEqual(ts, Timestamp(11, 2))
        ts -= Timestamp(1, 2)
        self.assertEqual(ts, Timestamp(10, 0))
        ts -= Timestamp(100, 5)
        self.assertEqual(ts, Timestamp(90, 5, -1))

        ts = Timestamp(281474976710655, 999999999)
        ts += Timestamp(0, 1)
        self.assertEqual(ts, Timestamp(281474976710655, 999999999))

        ts = Timestamp(10, 0)
        ts -= Timestamp(100, 0)
        self.assertEqual(ts, Timestamp(90, 0, -1))

        ts = Timestamp(10, 0)
        ts -= Timestamp(0, 1)
        self.assertEqual(ts, Timestamp(9, 999999999))

        ts = Timestamp(10, 500000000)
        ts += Timestamp(0, 500000000)
        self.assertEqual(ts, Timestamp(11, 0))

        ts = Timestamp(10, 500000000, -1)
        ts -= Timestamp(0, 500000000)
        self.assertEqual(ts, Timestamp(11, 0, -1))

        ts = Timestamp(10, 0, -1)
        ts += Timestamp(0, 500000000)
        self.assertEqual(ts, Timestamp(9, 500000000, -1))

    def test_addsub(self):
        """This tests addition and subtraction on timestamps."""

        tests_ts = [
            (Timestamp(10, 0), '+', Timestamp(1, 2), Timestamp(11, 2)),
            (Timestamp(11, 2), '-', Timestamp(1, 2), Timestamp(10, 0)),
            (Timestamp(11, 2), '-', Timestamp(1, 2), Timestamp(10, 0)),
            (Timestamp(10, 0), '-', Timestamp(11, 2), Timestamp(1, 2, -1)),
            (Timestamp(10, 0), '-', Timestamp(11, 2), Timestamp(1, 2, -1)),
            (Timestamp(10, 0), '-', Timestamp(11, 2), Timestamp(1, 2, -1)),
            (Timestamp(10, 0), '-', Timestamp(11, 2), Timestamp(1, 2, -1)),
            (Timestamp(11, 2), '-', Timestamp(10, 0), Timestamp(1, 2, 1)),
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
            (Timestamp(10, 10), '*', 0, Timestamp(0, 0)),
            (Timestamp(10, 10), '*', 10, Timestamp(100, 100)),
            (10, '*', Timestamp(10, 10), Timestamp(100, 100)),
            (Timestamp(10, 10), '*', (-10), Timestamp(100, 100, -1)),
            (Timestamp(10, 10, -1), '*', 10, Timestamp(100, 100, -1)),
            (Timestamp(100, 100), '//', 10, Timestamp(10, 10)),
            (Timestamp(100, 100), '//', -10, Timestamp(10, 10, -1)),
            (Timestamp(100, 100, -1), '//', 10, Timestamp(10, 10, -1)),
            (Timestamp(281474976710654, 0), '//', 281474976710655, Timestamp(0, 999999999)),
            (Timestamp(100, 100), '//', 10, Timestamp(10, 10)),
            (Timestamp(100, 100), '/', 10, Timestamp(10, 10)),
            (Timestamp(100, 100), '/', -10, Timestamp(10, 10, -1)),
            (Timestamp(100, 100, -1), '/', 10, Timestamp(10, 10, -1)),
            (Timestamp(281474976710654, 0), '/', 281474976710655, Timestamp(0, 999999999)),
            (Timestamp(100, 100), '/', 10, Timestamp(10, 10)),
            (Timestamp(10, 10), '*', 10, Timestamp(100, 100)),
            (10, '*', Timestamp(10, 10), Timestamp(100, 100)),
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
        self.assertLess(Timestamp(2, 0), 3)
        self.assertGreaterEqual(Timestamp(1, 0, 1), Timestamp(1, 0, -1))

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
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_nsec()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            self.assertEqual(ts_str, str(ts))

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
            self.assertEqual(ts_str, str(ts))

    def test_convert_sec_frac(self):
        """This tests that the conversion to and from TAI seconds with fractional parts works as expected."""

        tests_ts = [
            ("0.0", Timestamp(0, 0), "0.0"),
            ("0.1", Timestamp(0, 1000000000 // 10), "0.1"),
            ("-0.1", Timestamp(0, 1000000000 // 10, -1), "-0.1"),
            ("5", Timestamp(5, 0), "5.0"),
            ("5.1", Timestamp(5, 1000000000 // 10), "5.1"),
            ("-5.1", Timestamp(5, 1000000000 // 10, -1), "-5.1"),
            ("5.10000000", Timestamp(5, 1000000000 // 10), "5.1"),
            ("5.123456789", Timestamp(5, 123456789), "5.123456789"),
            ("5.000000001", Timestamp(5, 1), "5.000000001"),
            ("5.0000000001", Timestamp(5, 0), "5.0")
        ]

        for t in tests_ts:
            ts = Timestamp.from_sec_frac(t[0])
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
            (Timestamp(62135596800, 0, -1), "0001-01-01T00:00:00.000000000Z"),
            (Timestamp(1, 0, -1), "1969-12-31T23:59:59.000000000Z"),
            (Timestamp(0, 999999999, -1), "1969-12-31T23:59:59.000000001Z"),
            (Timestamp(0, 1, -1), "1969-12-31T23:59:59.999999999Z"),
            (Timestamp(0, 0, 1), "1970-01-01T00:00:00.000000000Z"),

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

            (Timestamp(283996818, 0), "1979-01-01T00:00:00.000000000Z"),  # 1979
            (Timestamp(253402300836, 999999999), "9999-12-31T23:59:59.999999999Z")
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
            (datetime(1, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(62135596800, 0, -1)),
            (datetime(1969, 12, 31, 23, 59, 59, 0, tz.gettz('UTC')), Timestamp(1, 0, -1)),
            (datetime(1969, 12, 31, 23, 59, 59, 1, tz.gettz('UTC')), Timestamp(0, 999999000, -1)),
            (datetime(1969, 12, 31, 23, 59, 59, 999999, tz.gettz('UTC')), Timestamp(0, 1000, -1)),
            (datetime(1970, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(0, 0)),
            (datetime(1983, 3, 29, 15, 45, 0, 0, tz.gettz('UTC')), Timestamp(417800721, 0)),
            (datetime(2017, 12, 5, 16, 33, 12, 196, tz.gettz('UTC')), Timestamp(1512491629, 196000)),
            (datetime(2514, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(17166988837, 0, 1)),
            # Stopping around here because high datetime values have a floating point error.
            # See https://stackoverflow.com/a/75582241.
        ]

        for t in tests:
            self.assertEqual(Timestamp.from_datetime(t[0]), t[1])

    def test_to_datetime(self):
        """Conversion to python's datetime object."""

        tests = [
            (datetime(1, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(62135596800, 0, -1)),
            (datetime(1969, 12, 31, 23, 59, 59, 0, tz.gettz('UTC')), Timestamp(1, 0, -1)),
            (datetime(1969, 12, 31, 23, 59, 59, 1, tz.gettz('UTC')), Timestamp(0, 999999000, -1)),
            (datetime(1969, 12, 31, 23, 59, 59, 999999, tz.gettz('UTC')), Timestamp(0, 1000, -1)),
            (datetime(1970, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(0, 0)),
            (datetime(1970, 1, 1, 0, 0, 0, 1, tz.gettz('UTC')), Timestamp(0, 1000)),
            (datetime(1983, 3, 29, 15, 45, 0, 0, tz.gettz('UTC')), Timestamp(417800721, 0)),
            (datetime(2017, 12, 5, 16, 33, 12, 196, tz.gettz('UTC')), Timestamp(1512491629, 196000)),
            (datetime(2017, 12, 5, 16, 33, 13, 0, tz.gettz('UTC')), Timestamp(1512491629, 999999999)),
            (datetime(2514, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(17166988837, 0, 1)),
            # Stopping around here because high datetime values have a floating point error.
            # See https://stackoverflow.com/a/75582241
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
                self.assertEqual(Timestamp.from_str(t[0]), t[1])

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

    def test_from_unix(self):
        tests = [
            ((Timestamp.MAX_SECONDS - 1, Timestamp.MAX_NANOSEC - 1, -1, False),  # 0 leap seconds
                Timestamp(Timestamp.MAX_SECONDS - 1, Timestamp.MAX_NANOSEC - 1, -1)),  # 0 leap seconds
            ((1000, 0, -1, False), Timestamp(1000, 0, -1)),    # 0 leap seconds
            ((63071999, 999999999, 1, False), Timestamp(63071999, 999999999)),  # 0 leap seconds
            ((63071999, 0, 1, True), Timestamp(63072009, 0)),  # 10 leap seconds at leap
            ((63072000, 0, 1, False), Timestamp(63072010, 0)),  # 10 leap seconds
            ((63072008, 999999999, 1, False), Timestamp(63072018, 999999999)),  # 10 leap seconds
            ((1512491592, 0, 1, False), Timestamp(1512491629, 0)),  # 37 leap seconds
            ((Timestamp.MAX_SECONDS - 1 - 37, Timestamp.MAX_NANOSEC - 1, 1, False),
                Timestamp(Timestamp.MAX_SECONDS - 1, Timestamp.MAX_NANOSEC - 1)),  # 37 leap seconds
        ]

        for t in tests:
            self.assertEqual(Timestamp.from_unix(*t[0]), t[1])

    def test_to_unix(self):
        tests = [
            (Timestamp(Timestamp.MAX_SECONDS - 1, Timestamp.MAX_NANOSEC - 1, -1),  # 0 leap seconds
                (Timestamp.MAX_SECONDS - 1, Timestamp.MAX_NANOSEC - 1, -1, False)),  # 0 leap seconds
            (Timestamp(1000, 0, -1), (1000, 0, -1, False)),  # 0 leap seconds
            (Timestamp(63072008, 999999999), (63072008, 999999999, 1, False)),  # 0 leap seconds
            (Timestamp(63072009, 0), (63071999, 0, 1, True)),  # 10 leap seconds at leap
            (Timestamp(63072010, 0), (63072000, 0, 1, False)),  # 10 leap seconds
            (Timestamp(1512491629, 0), (1512491592, 0, 1, False)),  # 37 leap seconds
            (Timestamp(Timestamp.MAX_SECONDS - 1, Timestamp.MAX_NANOSEC - 1),
                (Timestamp.MAX_SECONDS - 1 - 37, Timestamp.MAX_NANOSEC - 1, 1, False)),  # 37 leap seconds
        ]

        for t in tests:
            self.assertEqual(t[0].to_unix(), t[1])

    def test_to_unix_float(self):
        tests = [
            (Timestamp(63072008, 999999999), 63072008 + 999999999 / 1000000000),
            (Timestamp(63072009, 0), 63071999),
            (Timestamp(1000, 0, -1), -1000)
        ]

        for t in tests:
            self.assertEqual(t[0].to_unix_float(), t[1])
