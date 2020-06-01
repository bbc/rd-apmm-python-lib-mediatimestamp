# Copyright 2019 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

import unittest
from fractions import Fraction

from mediatimestamp import (
    TimeOffset,
    Timestamp,
    SupportsMediaTimeOffset,
    mediatimeoffset,
    SupportsMediaTimestamp,
    mediatimestamp,
    TimeValue)


class TestTimeValue(unittest.TestCase):
    def test_from_int(self):
        tv = TimeValue(100, rate=Fraction(25))
        self.assertEqual(tv.value, 100)
        self.assertEqual(tv.rate, Fraction(25))

    def test_from_timeoffset(self):
        tv = TimeValue(TimeOffset(4), rate=None)
        self.assertEqual(tv.value, TimeOffset(4))
        self.assertIsNone(tv.rate)

    def test_from_timestamp(self):
        tv = TimeValue(Timestamp(4), rate=None)
        self.assertEqual(tv.value, Timestamp(4))
        self.assertIsNone(tv.rate)

    def test_from_timevalue(self):
        tv_in = TimeValue(100, rate=Fraction(25))
        tv = TimeValue(tv_in)
        self.assertEqual(tv.value, 100)
        self.assertEqual(tv.rate, Fraction(25))

    def test_from_timeoffset_to_count(self):
        tv = TimeValue(TimeOffset(4), rate=Fraction(25))
        self.assertIsInstance(tv.value, int)
        self.assertEqual(tv.value, 100)
        self.assertEqual(tv.rate, Fraction(25))

    def test_from_timevalue_rate_change(self):
        tv_in = TimeValue(100, rate=Fraction(25))
        tv = TimeValue(tv_in, rate=Fraction(100))
        self.assertEqual(tv.value, 400)
        self.assertEqual(tv.rate, Fraction(100))

    def test_unsupported_type(self):
        with self.assertRaises(TypeError):
            TimeValue(str(10))

    def test_as_timeoffset(self):
        tv = TimeValue(TimeOffset(4), rate=Fraction(25))
        to = tv.as_timeoffset()
        self.assertIsInstance(to, TimeOffset)
        self.assertEqual(to, TimeOffset(4))

        tv = TimeValue(Timestamp(4), rate=Fraction(25))
        to = tv.as_timeoffset()
        self.assertIsInstance(to, TimeOffset)
        self.assertEqual(to, TimeOffset(4))

        tv = TimeValue(100, rate=Fraction(25))
        to = tv.as_timeoffset()
        self.assertIsInstance(to, TimeOffset)
        self.assertEqual(to, TimeOffset(4))

    def test_mediatimeoffset(self):
        tv = TimeValue(TimeOffset(4), rate=Fraction(25))
        self.assertIsInstance(tv, SupportsMediaTimeOffset)
        to = mediatimeoffset(tv)
        self.assertIsInstance(to, TimeOffset)
        self.assertEqual(to, TimeOffset(4))

        tv = TimeValue(Timestamp(4), rate=Fraction(25))
        self.assertIsInstance(tv, SupportsMediaTimeOffset)
        to = mediatimeoffset(tv)
        self.assertIsInstance(to, TimeOffset)
        self.assertEqual(to, TimeOffset(4))

        tv = TimeValue(100, rate=Fraction(25))
        self.assertIsInstance(tv, SupportsMediaTimeOffset)
        to = mediatimeoffset(tv)
        self.assertIsInstance(to, TimeOffset)
        self.assertEqual(to, TimeOffset(4))

    def test_as_timestamp(self):
        tv = TimeValue(Timestamp(4), rate=Fraction(25))
        ts = tv.as_timestamp()
        self.assertIsInstance(ts, Timestamp)
        self.assertEqual(ts, Timestamp(4))

        tv = TimeValue(TimeOffset(4), rate=Fraction(25))
        ts = tv.as_timestamp()
        self.assertIsInstance(ts, Timestamp)
        self.assertEqual(ts, Timestamp(4))

        tv = TimeValue(100, rate=Fraction(25))
        ts = tv.as_timestamp()
        self.assertIsInstance(ts, Timestamp)
        self.assertEqual(ts, Timestamp(4))

    def test_mediatimestamp(self):
        tv = TimeValue(Timestamp(4), rate=Fraction(25))
        self.assertIsInstance(tv, SupportsMediaTimestamp)
        ts = mediatimestamp(tv)
        self.assertIsInstance(ts, Timestamp)
        self.assertEqual(ts, Timestamp(4))

        tv = TimeValue(TimeOffset(4), rate=Fraction(25))
        self.assertIsInstance(tv, SupportsMediaTimestamp)
        ts = mediatimestamp(tv)
        self.assertIsInstance(ts, Timestamp)
        self.assertEqual(ts, Timestamp(4))

        tv = TimeValue(100, rate=Fraction(25))
        self.assertIsInstance(tv, SupportsMediaTimestamp)
        ts = mediatimestamp(tv)
        self.assertIsInstance(ts, Timestamp)
        self.assertEqual(ts, Timestamp(4))

    def test_as_count(self):
        tv = TimeValue(100)
        ct = tv.as_count()
        self.assertEqual(ct, 100)

        tv = TimeValue(TimeOffset(4), rate=Fraction(25))
        ct = tv.as_count()
        self.assertEqual(ct, 100)

    def test_as_but_no_rate(self):
        tv = TimeValue(TimeOffset(4))
        with self.assertRaises(ValueError):
            tv.as_count()

        tv = TimeValue(100)
        with self.assertRaises(ValueError):
            tv.as_timeoffset()

    def test_from_str(self):
        cases = [
            ("-100", TimeValue(-100)),
            ("0", TimeValue(0)),
            ("100", TimeValue(100)),

            ("100@25", TimeValue(100, rate=Fraction(25))),
            ("100@30000/1001", TimeValue(100, rate=Fraction(30000, 1001))),

            ("-4:0", TimeValue(TimeOffset(4, sign=-1))),
            ("0:0", TimeValue(TimeOffset(0))),
            ("4:0", TimeValue(TimeOffset(4))),

            ("4:0@25", TimeValue(100, rate=Fraction(25))),
            ("4:0@30000/1001", TimeValue(120, rate=Fraction(30000, 1001))),
        ]

        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(TimeValue.from_str(case[0]), case[1])

    def test_from_str_rate(self):
        tv = TimeValue.from_str("100@25", rate=Fraction(100))
        self.assertEqual(tv, TimeValue(100, rate=Fraction(25)))

        tv = TimeValue.from_str("100", rate=Fraction(100))
        self.assertEqual(tv, TimeValue(100, rate=Fraction(100)))

    def test_from_str_invalid(self):
        cases = [
            "100@25@",
            "100/30000/1001",
            "abc",
        ]

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    TimeValue.from_str(case)

    def test_to_str(self):
        cases = [
            ("-100", TimeValue(-100), True),
            ("0", TimeValue(0), True),
            ("100", TimeValue(100), True),

            ("100@25", TimeValue(100, rate=Fraction(25)), True),
            ("100", TimeValue(100, rate=Fraction(25)), False),
            ("100@30000/1001", TimeValue(100, rate=Fraction(30000, 1001)), True),

            ("-4:0", TimeValue(TimeOffset(4, sign=-1)), True),
            ("0:0", TimeValue(TimeOffset(0)), True),
            ("4:0", TimeValue(TimeOffset(4)), True),
        ]

        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(case[0], case[1].to_str(include_rate=case[2]))

    def test_compare(self):
        self.assertEqual(TimeValue(1), TimeValue(1))
        self.assertNotEqual(TimeValue(1), TimeValue(2))
        self.assertLess(TimeValue(1), TimeValue(2))
        self.assertLessEqual(TimeValue(1), TimeValue(1))
        self.assertGreater(TimeValue(2), TimeValue(1))
        self.assertGreaterEqual(TimeValue(2), TimeValue(2))
        self.assertNotEqual(TimeValue(2), TimeValue(3))
        self.assertEqual(TimeValue(TimeOffset(4)), TimeValue(TimeOffset(4)))

    def test_compare_with_convert(self):
        self.assertEqual(TimeValue(100, rate=Fraction(25)), TimeValue(TimeOffset(4)))
        self.assertEqual(TimeValue(TimeOffset(4)), TimeValue(100, rate=Fraction(25)))

    def test_compare_no_rate(self):
        with self.assertRaises(ValueError):
            TimeValue(100) == TimeValue(TimeOffset(4))

    def test_equality_none(self):
        none_value = None
        self.assertFalse(TimeValue(1) == none_value)
        self.assertTrue(TimeValue(1) != none_value)

    def test_addsub(self):
        cases = [
            (TimeValue(50), '+', TimeValue(50),
                TimeValue(100)),
            (TimeValue(50, rate=Fraction(25)), '+', TimeValue(TimeOffset(2)),
                TimeValue(100, rate=Fraction(25))),
            (TimeValue(TimeOffset(2)), '+', TimeValue(TimeOffset(2)),
                TimeValue(TimeOffset(4))),

            (TimeValue(50), '-', TimeValue(50),
                TimeValue(0)),
            (TimeValue(50, rate=Fraction(25)), '-', TimeValue(TimeOffset(2)),
                TimeValue(0, rate=Fraction(25))),
            (TimeValue(TimeOffset(2)), '-', TimeValue(TimeOffset(2)),
                TimeValue(TimeOffset(0))),
        ]

        for case in cases:
            with self.subTest(case=case):
                if case[1] == '+':
                    result = case[0] + case[2]
                else:
                    result = case[0] - case[2]

                self.assertEqual(result, case[3],
                                 msg="{!r} {} {!r} = {!r}, expected {!r}".format(
                                     case[0], case[1], case[2], result, case[3]))

    def test_addsub_no_rate(self):
        cases = [
            (TimeValue(50), '+', TimeValue(TimeOffset(2))),
            (TimeValue(TimeOffset(2)), '+', TimeValue(50)),

            (TimeValue(50), '-', TimeValue(TimeOffset(2))),
            (TimeValue(TimeOffset(2)), '-', TimeValue(50)),
        ]

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    if case[1] == '+':
                        case[0] + case[2]
                    else:
                        case[0] - case[2]

    def test_multdiv(self):
        cases = [
            (TimeValue(50), '*', 2,
                TimeValue(100)),
            (TimeValue(TimeOffset(2)), '*', 2,
                TimeValue(TimeOffset(4))),

            (2, '*', TimeValue(50),
                TimeValue(100)),
            (2, '*', TimeValue(TimeOffset(2)),
                TimeValue(TimeOffset(4))),

            (TimeValue(50), '/', 2,
                TimeValue(25)),
            (TimeValue(TimeOffset(2)), '/', 2,
                TimeValue(TimeOffset(1))),

            (TimeValue(25), '/', 2,
                TimeValue(12)),
            (TimeValue(25), '//', 2,
                TimeValue(12)),
        ]

        for case in cases:
            with self.subTest(case=case):
                if case[1] == '*':
                    result = case[0] * case[2]
                elif case[1] == '/':
                    result = case[0] / case[2]
                else:
                    result = case[0] // case[2]

                self.assertEqual(result, case[3],
                                 msg="{!r} {} {!r} = {!r}, expected {!r}".format(
                                     case[0], case[1], case[2], result, case[3]))

    def test_multdiv_not_int(self):
        cases = [
            (TimeValue(50), '*', TimeValue(50)),
            (TimeValue(50), '/', TimeValue(50)),
            (TimeValue(50), '//', TimeValue(50)),
        ]

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    if case[1] == '*':
                        case[0] * case[2]
                    elif case[1] == '/':
                        case[0] / case[2]
                    else:
                        case[0] // case[2]

    def test_immutable(self):
        tv = TimeValue(0)
        with self.assertRaises(ValueError):
            tv._value = 1

        with self.assertRaises(ValueError):
            tv._rate = Fraction(50)

    def test_hashable(self):
        tv1 = TimeValue(0)
        tv2 = TimeValue.from_str("0:20000000000@50")
        self.assertNotEqual(hash(tv1), hash(tv2))
