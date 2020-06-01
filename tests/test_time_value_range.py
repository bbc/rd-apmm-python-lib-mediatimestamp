# Copyright 2019 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

import unittest
from fractions import Fraction

from mediatimestamp import (
    TimeOffset, TimeRange, Timestamp, SupportsMediaTimeRange, mediatimerange,
    CountRange, TimeValue, TimeValueRange)


class TestTimeValueRange(unittest.TestCase):
    def test_from_timerange(self):
        tvr = TimeValueRange(TimeRange(Timestamp(0), Timestamp(1)))
        self.assertEqual(tvr, TimeValueRange(TimeValue(TimeOffset(0)), TimeValue(TimeOffset(1))))

        tvr = TimeValueRange(TimeRange(Timestamp(0), Timestamp(1)), rate=Fraction(25))
        self.assertEqual(tvr, TimeValueRange(TimeValue(0), TimeValue(25), rate=Fraction(25)))

    def test_from_countrange(self):
        tvr = TimeValueRange(CountRange(0, 25))
        self.assertEqual(tvr, TimeValueRange(TimeValue(0), TimeValue(25)))

    def test_from_int(self):
        tvr = TimeValueRange(0, 25)
        self.assertEqual(tvr, TimeValueRange(TimeValue(0), TimeValue(25)))

    def test_from_timeoffset(self):
        tvr = TimeValueRange(TimeOffset(0), TimeOffset(1))
        self.assertEqual(tvr._start, TimeOffset(0))
        self.assertEqual(tvr._end, TimeOffset(1))
        self.assertEqual(tvr._inclusivity, TimeValueRange.INCLUSIVE)
        self.assertIsNone(tvr._rate)

        tvr = TimeValueRange(TimeOffset(0), TimeOffset(1), rate=Fraction(25))
        self.assertEqual(tvr, TimeValueRange(TimeValue(0), TimeValue(25), rate=Fraction(25)))

    def test_norm_never(self):
        tvr = TimeValueRange(0, 0, TimeValueRange.EXCLUSIVE)
        self.assertEqual(tvr, TimeValueRange.never())

    def test_override_rate(self):
        tvr = TimeValueRange(TimeValue(100, rate=Fraction(25)), TimeValue(200, rate=Fraction(25)),
                             rate=Fraction(100))
        self.assertEqual(tvr, TimeValueRange(TimeValue(400), TimeValue(800), rate=Fraction(100)))

    def test_add_rate(self):
        tvr = TimeValueRange(TimeValue(100), TimeValue(200), rate=Fraction(25))
        self.assertEqual(tvr, TimeValueRange(TimeValue(100, rate=Fraction(25)),
                         TimeValue(200, rate=Fraction(25)), rate=Fraction(25)))

    def test_as_timerange(self):
        tvr = TimeValueRange(TimeRange(Timestamp(0), Timestamp(1)))
        self.assertEqual(tvr.as_timerange(), TimeRange(Timestamp(0), Timestamp(1)))

        tvr = TimeValueRange(0, 25, rate=Fraction(25))
        self.assertEqual(tvr.as_timerange(), TimeRange.from_str("[0:0_1:40000000)"))
        tvr = TimeValueRange(TimeRange.from_str("[0:0_1:40000000)"), rate=Fraction(25))
        self.assertEqual(tvr.as_timerange(), TimeRange.from_str("[0:0_1:40000000)"))

    def test_mediatimerange(self):
        tvr = TimeValueRange(TimeRange(Timestamp(0), Timestamp(1)))
        self.assertIsInstance(tvr, SupportsMediaTimeRange)
        self.assertEqual(mediatimerange(tvr), TimeRange(Timestamp(0), Timestamp(1)))

        tvr = TimeValueRange(0, 25, rate=Fraction(25))
        self.assertIsInstance(tvr, SupportsMediaTimeRange)
        self.assertEqual(mediatimerange(tvr), TimeRange.from_str("[0:0_1:40000000)"))

        tvr = TimeValueRange(TimeRange.from_str("[0:0_1:40000000)"), rate=Fraction(25))
        self.assertIsInstance(tvr, SupportsMediaTimeRange)
        self.assertEqual(mediatimerange(tvr), TimeRange.from_str("[0:0_1:40000000)"))

    def test_as_countrange(self):
        tvr = TimeValueRange(0, 25)
        self.assertEqual(tvr.as_count_range(), CountRange(0, 25))

        tvr = TimeValueRange(TimeRange(Timestamp(0), Timestamp(1)), rate=Fraction(25))
        self.assertEqual(tvr.as_count_range(), CountRange(0, 25))

    def test_never(self):
        rng = TimeValueRange.never()

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(1, rng)

        self.assertTrue(rng.is_empty())
        self.assertEqual(rng.to_str(), "()")

    def test_eternity(self):
        alltime = TimeValueRange.eternity()

        self.assertIn(-1, alltime)
        self.assertIn(0, alltime)
        self.assertIn(1, alltime)

        self.assertEqual(alltime.to_str(), "_")

    def test_bounded_on_right_inclusive(self):
        rng = TimeValueRange.from_end(100)

        self.assertIn(-1, rng)
        self.assertIn(0, rng)
        self.assertIn(99, rng)
        self.assertIn(100, rng)
        self.assertNotIn(101, rng)

        self.assertEqual(rng.to_str(), "_101)")

    def test_bounded_on_right_exclusive(self):
        rng = TimeValueRange.from_end(100, inclusivity=TimeValueRange.EXCLUSIVE)

        self.assertIn(-1, rng)
        self.assertIn(0, rng)
        self.assertIn(99, rng)
        self.assertNotIn(100, rng)
        self.assertNotIn(101, rng)

        self.assertEqual(rng.to_str(), "_100)")

    def test_bounded_on_left_inclusive(self):
        rng = TimeValueRange.from_start(100)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertIn(100, rng)
        self.assertIn(101, rng)

        self.assertEqual(rng.to_str(), "[100_")

    def test_bounded_on_left_exclusive(self):
        rng = TimeValueRange.from_start(100, inclusivity=TimeValueRange.EXCLUSIVE)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertNotIn(100, rng)
        self.assertIn(101, rng)

        self.assertEqual(rng.to_str(), "[101_")

    def test_bounded_inclusive(self):
        rng = TimeValueRange(100, 200)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertIn(100, rng)
        self.assertIn(101, rng)
        self.assertIn(199, rng)
        self.assertIn(200, rng)
        self.assertNotIn(201, rng)

        self.assertEqual(rng.to_str(), "[100_201)")

    def test_bounded_exclusive(self):
        rng = TimeValueRange(100, 200, inclusivity=TimeValueRange.EXCLUSIVE)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertNotIn(100, rng)
        self.assertIn(101, rng)
        self.assertIn(199, rng)
        self.assertNotIn(200, rng)
        self.assertNotIn(201, rng)

        self.assertEqual(rng.to_str(), "[101_200)")

    def test_single_value(self):
        rng = TimeValueRange.from_single_value(100)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertIn(100, rng)
        self.assertNotIn(101, rng)

        self.assertEqual(rng.to_str(), "[100_101)")

    def test_from_str(self):
        tests = [
            ("()", TimeValueRange.never()),
            ("[]", TimeValueRange.never()),
            ("", TimeValueRange.never()),
            ("_", TimeValueRange.eternity()),
            ("_200", TimeValueRange.from_end(200)),
            ("[_200]", TimeValueRange.from_end(200, inclusivity=TimeValueRange.INCLUSIVE)),
            ("(_200)", TimeValueRange.from_end(200, inclusivity=TimeValueRange.EXCLUSIVE)),
            ("100_", TimeValueRange.from_start(100)),
            ("[100_]", TimeValueRange.from_start(100, inclusivity=TimeValueRange.INCLUSIVE)),
            ("(100_)", TimeValueRange.from_start(100, inclusivity=TimeValueRange.EXCLUSIVE)),
            ("100_200", TimeValueRange(100, 200)),
            ("[100_200]", TimeValueRange(100, 200, inclusivity=TimeValueRange.INCLUSIVE)),
            ("(100_200)", TimeValueRange(100, 200, inclusivity=TimeValueRange.EXCLUSIVE)),
            ("(100_200]", TimeValueRange(100, 200, inclusivity=TimeValueRange.INCLUDE_END)),
            ("[100_200)", TimeValueRange(100, 200, inclusivity=TimeValueRange.INCLUDE_START)),
            ("200", TimeValueRange.from_single_value(200)),

            ("[-100_200)", TimeValueRange(-100, 200, inclusivity=TimeValueRange.INCLUDE_START)),
            ("[-200_-100)", TimeValueRange(-200, -100, inclusivity=TimeValueRange.INCLUDE_START)),

            ("[100_200]@25", TimeValueRange(100, 200, inclusivity=TimeValueRange.INCLUSIVE, rate=Fraction(25))),
            ("[4:0_8:0]@25", TimeValueRange(100, 200, inclusivity=TimeValueRange.INCLUSIVE, rate=Fraction(25))),
            ("[4:0_8:0]", TimeValueRange(TimeOffset(4), TimeOffset(8), inclusivity=TimeValueRange.INCLUSIVE)),
        ]

        for (s, tr) in tests:
            self.assertEqual(tr, TimeValueRange.from_str(s))

    def test_to_str(self):
        cases = [
            ("[100_201)", TimeValueRange(100, 200), True),
            ("[100_201)@25", TimeValueRange(100, 200, rate=Fraction(25)), True),
            ("[100_201)", TimeValueRange(100, 200, rate=Fraction(25)), False),

            ("[4:0_8:0]", TimeValueRange(TimeOffset(4), TimeOffset(8)), True),

            ("[100_201)@25", TimeValueRange(TimeValue(100),
                                            TimeValue(200, rate=Fraction(25))), True),
            ("[100_201)@25", TimeValueRange(TimeValue(100, rate=Fraction(25)),
                                            TimeValue(200)), True),
        ]

        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(case[0], case[1].to_str(include_rate=case[2]))

    def test_subrange(self):
        a = 50
        b = 100
        c = 200
        d = 250

        self.assertTrue(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertFalse(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertTrue(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(a, b, inclusivity=TimeValueRange.EXCLUSIVE)))
        self.assertTrue(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(a, b, inclusivity=TimeValueRange.EXCLUSIVE)))

        self.assertTrue(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertFalse(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertTrue(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE)))
        self.assertTrue(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE)))

        self.assertTrue(TimeValueRange(a, d, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertTrue(TimeValueRange(a, d, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertTrue(TimeValueRange(a, d, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE)))
        self.assertTrue(TimeValueRange(a, d, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE)))

        self.assertFalse(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(b, d, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertFalse(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(b, d, inclusivity=TimeValueRange.INCLUSIVE)))
        self.assertFalse(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).contains_subrange(
            TimeValueRange(b, d, inclusivity=TimeValueRange.EXCLUSIVE)))
        self.assertFalse(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).contains_subrange(
            TimeValueRange(b, d, inclusivity=TimeValueRange.EXCLUSIVE)))

    def test_intersection(self):
        a = 50
        b = 100
        c = 200
        d = 250

        self.assertEqual(TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE).intersect_with(
                            TimeValueRange(c, d, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange.never())

        self.assertEqual(TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE).intersect_with(
                            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange.from_single_value(b))

        self.assertEqual(TimeValueRange(a, b, inclusivity=TimeValueRange.EXCLUSIVE).intersect_with(
                            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange.never())

        self.assertEqual(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).intersect_with(
                            TimeValueRange(b, d, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE))

        self.assertEqual(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).intersect_with(
                            TimeValueRange(b, d, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUDE_START))

        self.assertEqual(TimeValueRange(a, c, inclusivity=TimeValueRange.INCLUSIVE).intersect_with(
                            TimeValueRange(b, d, inclusivity=TimeValueRange.EXCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUDE_END))

        self.assertEqual(TimeValueRange(a, c, inclusivity=TimeValueRange.EXCLUSIVE).intersect_with(
                            TimeValueRange(b, d, inclusivity=TimeValueRange.EXCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE))

        self.assertEqual(TimeValueRange(a, d, inclusivity=TimeValueRange.INCLUSIVE).intersect_with(
                            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE))

        self.assertEqual(TimeValueRange(a, d, inclusivity=TimeValueRange.EXCLUSIVE).intersect_with(
                            TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.INCLUSIVE))

        self.assertEqual(TimeValueRange(a, d, inclusivity=TimeValueRange.INCLUSIVE).intersect_with(
                            TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE))

        self.assertEqual(TimeValueRange(a, d, inclusivity=TimeValueRange.EXCLUSIVE).intersect_with(
                            TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE)),
                         TimeValueRange(b, c, inclusivity=TimeValueRange.EXCLUSIVE))

        self.assertEqual(TimeValueRange.eternity().intersect_with(
                            TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE))

        self.assertEqual(TimeValueRange.eternity().intersect_with(
                            TimeValueRange(a, b, inclusivity=TimeValueRange.EXCLUSIVE)),
                         TimeValueRange(a, b, inclusivity=TimeValueRange.EXCLUSIVE))

        self.assertEqual(TimeValueRange.never().intersect_with(
                            TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE)),
                         TimeValueRange.never())

        self.assertEqual(TimeValueRange.never().intersect_with(
                            TimeValueRange(a, b, inclusivity=TimeValueRange.EXCLUSIVE)),
                         TimeValueRange.never())

        self.assertEqual(TimeValueRange.never().intersect_with(
                            TimeValueRange.eternity()),
                         TimeValueRange.never())

    def test_length(self):
        a = 50
        b = 100

        rng = TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE)
        self.assertEqual(rng.length_as_count(), b - a + 1)

        rng = TimeValueRange(None, b, inclusivity=TimeValueRange.INCLUSIVE)
        self.assertEqual(rng.length_as_count(), float("inf"))

        rng = TimeValueRange(a, None, inclusivity=TimeValueRange.INCLUSIVE)
        self.assertEqual(rng.length_as_count(), float("inf"))

        rng = TimeValueRange(None, None, inclusivity=TimeValueRange.INCLUSIVE)
        self.assertEqual(rng.length_as_count(), float("inf"))

        rng = TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE)
        self.assertEqual(rng, TimeValueRange(a, b, inclusivity=TimeValueRange.INCLUSIVE))

    def test_repr(self):
        """This tests that the repr function turns time ranges into `eval`-able strings."""
        test_trs = [
            (TimeValueRange.from_str("(100_200)"),
             "mediatimestamp.time_value_range.TimeValueRange.from_str('[101_200)')"),
            (TimeValueRange.from_str("[100_200]"),
             "mediatimestamp.time_value_range.TimeValueRange.from_str('[100_201)')"),
            (TimeValueRange.from_str("[100_"),
             "mediatimestamp.time_value_range.TimeValueRange.from_str('[100_')")
        ]

        for t in test_trs:
            self.assertEqual(repr(t[0]), t[1])

    def test_comparisons(self):
        # Test data format:
        #  (a, b,
        #   (starts_inside, ends_inside, is_earlier, is_later,
        #    starts_earlier, starts_later, ends_earlier, ends_later,
        #    overlaps_with, is_contiguous_with))
        test_data = [
            (TimeValueRange.from_str("_"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeValueRange.from_str("_"), TimeValueRange.from_str("[0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeValueRange.from_str("_"), TimeValueRange.from_str("_0]"),
             (True, False, False, False, False, False, False, True, True, True)),
            (TimeValueRange.from_str("_"), TimeValueRange.from_str("[0_10)"),
             (False, False, False, False, True, False, False, True, True, True)),

            (TimeValueRange.from_str("_5)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("_5)"), TimeValueRange.from_str("[0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeValueRange.from_str("_5)"), TimeValueRange.from_str("_0]"),
             (True, False, False, False, False, False, False, True, True, True)),
            (TimeValueRange.from_str("_5)"), TimeValueRange.from_str("_10]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("_5)"), TimeValueRange.from_str("[0_10)"),
             (False, True, False, False, True, False, True, False, True, True)),

            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("[0_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("_0]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("_0)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("_10]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("[0_10)"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("(0_10)"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("[5_10)"),
             (False, False, True, False, True, False, True, False, False, False)),

            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("[0_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("(0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("[5_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("_0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("_10]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("[0_10)"),
             (True, False, False, False, False, False, False, True, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("(0_10)"),
             (False, False, False, False, True, False, False, True, True, True)),
            (TimeValueRange.from_str("[0_)"), TimeValueRange.from_str("[5_10)"),
             (False, False, False, False, True, False, False, True, True, True)),

            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("[0_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("(0_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("[5_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("(5_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("_0]"),
             (False, False, False, True, False, True, False, True, False, False)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, False)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("_10]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("[0_10)"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("(0_10)"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[5_)"), TimeValueRange.from_str("[5_10)"),
             (True, False, False, False, False, False, False, True, True, True)),

            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("(0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[10_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("(10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("_0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("_10]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("_10)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[0_10)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("(0_10)"),
             (False, True, False, False, True, False, False, False, True, True)),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[5_10)"),
             (False, True, False, False, True, False, False, False, True, True)),

            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("[0_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("(0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("[10_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("(10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("_0]"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, False)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("_10]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("_10)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("[0_10)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("(0_10)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (TimeValueRange.from_str("(0_10)"), TimeValueRange.from_str("[5_10)"),
             (False, True, False, False, True, False, False, False, True, True)),

            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("(0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("(10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("_0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("_10]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("_10)"),
             (True, True, False, False, False, True, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[0_10)"),
             (True, True, False, False, False, False, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("(0_10)"),
             (False, True, False, False, True, False, True, False, True, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[5_10)"),
             (False, False, True, False, True, False, True, False, False, True)),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("(5_10)"),
             (False, False, True, False, True, False, True, False, False, False)),

            (TimeValueRange.never(), TimeValueRange.from_str("_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("[0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("(0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("[10_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("(10_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("_0]"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("_0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("_10]"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("[0_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("(0_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("[5_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (TimeValueRange.never(), TimeValueRange.from_str("(5_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
        ]
        functions = ("starts_inside_range",
                     "ends_inside_range",
                     "is_earlier_than_range",
                     "is_later_than_range",
                     "starts_earlier_than_range",
                     "starts_later_than_range",
                     "ends_earlier_than_range",
                     "ends_later_than_range",
                     "overlaps_with_range",
                     "is_contiguous_with_range")

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
            (TimeValueRange.from_str("_"), 0,
             TimeValueRange.from_str("_0)"), TimeValueRange.from_str("[0_")),
            (TimeValueRange.from_str("[0_"), 10,
             TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[10_")),
            (TimeValueRange.from_str("_10)"), 0,
             TimeValueRange.from_str("_0)"), TimeValueRange.from_str("[0_10)")),
            (TimeValueRange.from_str("[0_10)"), 5,
             TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[5_10)")),
            (TimeValueRange.from_str("[0_10]"), 5,
             TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[5_10]")),
            (TimeValueRange.from_str("(0_10)"), 5,
             TimeValueRange.from_str("(0_5)"), TimeValueRange.from_str("[5_10)")),
            (TimeValueRange.from_str("(0_10]"), 5,
             TimeValueRange.from_str("(0_5)"), TimeValueRange.from_str("[5_10]")),
            (TimeValueRange.from_str("[0]"), 0,
             TimeValueRange.never(), TimeValueRange.from_str("[0_0]")),
            (TimeValueRange.from_str("[0_10)"), 0,
             TimeValueRange.never(), TimeValueRange.from_str("[0_10)")),
            (TimeValueRange.from_str("[0_10]"), 10,
             TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[10]")),
        ]

        for (tr, ts, left, right) in test_data:
            with self.subTest(tr=tr, ts=ts, expected=(left, right)):
                self.assertEqual(tr.split_at(ts), (left, right))

        test_data = [
            (TimeValueRange.from_str("[0_10)"), 11),
            (TimeValueRange.from_str("[0_10)"), 10),
        ]

        for (tr, ts) in test_data:
            with self.subTest(tr=tr, ts=ts):
                with self.assertRaises(ValueError):
                    tr.split_at(ts)

    def test_extend_to_encompass(self):
        test_data = [
            (TimeValueRange.from_str("()"), TimeValueRange.from_str("()"),
             TimeValueRange.from_str("()")),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[10]"),
             TimeValueRange.from_str("[0_10]")),
            (TimeValueRange.from_str("_"), TimeValueRange.from_str("[0]"),
             TimeValueRange.from_str("_")),
            (TimeValueRange.from_str("_"), TimeValueRange.from_str("()"),
             TimeValueRange.from_str("_")),
            (TimeValueRange.from_str("()"), TimeValueRange.from_str("_"),
             TimeValueRange.from_str("_")),
            (TimeValueRange.from_str("_10)"), TimeValueRange.from_str("[0_"),
             TimeValueRange.from_str("_")),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[5_"),
             TimeValueRange.from_str("[0_")),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[5_15)"),
             TimeValueRange.from_str("[0_15)")),
            (TimeValueRange.from_str("[0_10)"), TimeValueRange.from_str("[10_15)"),
             TimeValueRange.from_str("[0_15)")),
            (TimeValueRange.from_str("()"), TimeValueRange.from_str("[5_"),
             TimeValueRange.from_str("[5_")),
            (TimeValueRange.from_str("()"), TimeValueRange.from_str("[5_15)"),
             TimeValueRange.from_str("[5_15)")),
            (TimeValueRange.from_str("()"), TimeValueRange.from_str("_15)"),
             TimeValueRange.from_str("_15)")),

            # discontiguous
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("(0_"),
             TimeValueRange.from_str("_")),
            (TimeValueRange.from_str("(0_"), TimeValueRange.from_str("_0)"),
             TimeValueRange.from_str("_")),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("(5_15)"),
             TimeValueRange.from_str("[0_15)")),
            (TimeValueRange.from_str("(5_15)"), TimeValueRange.from_str("[0_5)"),
             TimeValueRange.from_str("[0_15)")),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[10_15)"),
             TimeValueRange.from_str("[0_15)")),
            (TimeValueRange.from_str("[10_15)"), TimeValueRange.from_str("[0_5)"),
             TimeValueRange.from_str("[0_15)")),
        ]

        for (first, second, expected) in test_data:
            with self.subTest(first=first, second=second, expected=expected):
                self.assertEqual(first.extend_to_encompass_range(second), expected)

    def test_union_raises(self):
        # discontiguous part of test_extend_to_encompass raises for a union
        test_data = [
            (TimeValueRange.from_str("_0)"), TimeValueRange.from_str("(0_")),
            (TimeValueRange.from_str("(0_"), TimeValueRange.from_str("_0)")),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("(5_15)")),
            (TimeValueRange.from_str("(5_15)"), TimeValueRange.from_str("[0_5)")),
            (TimeValueRange.from_str("[0_5)"), TimeValueRange.from_str("[10_15)")),
            (TimeValueRange.from_str("[10_15)"), TimeValueRange.from_str("[0_5)")),
        ]

        for (first, second) in test_data:
            with self.subTest(first=first, second=second):
                with self.assertRaises(ValueError):
                    first.union_with_range(second)

    def test_immutable(self):
        tvr = TimeValueRange(0, 1)
        with self.assertRaises(ValueError):
            tvr._start = 1

        with self.assertRaises(ValueError):
            tvr._end = 1

        with self.assertRaises(ValueError):
            tvr._inclusivity = CountRange.INCLUSIVE

        with self.assertRaises(ValueError):
            tvr._rate = Fraction(50)

    def test_iterable(self):
        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.INCLUDE_START)
        with self.subTest(tvr=tvr):
            values = [tv for tv in tvr]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in range(0, 10)])

        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.INCLUSIVE)
        with self.subTest(tvr=tvr):
            values = [tv for tv in tvr]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in range(0, 11)])

        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.EXCLUSIVE)
        with self.subTest(tvr=tvr):
            values = [tv for tv in tvr]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in range(1, 10)])

        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.INCLUDE_END)
        with self.subTest(tvr=tvr):
            values = [tv for tv in tvr]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in range(1, 11)])

        tvr = TimeValueRange.from_str("[0:0_1:0)")
        with self.subTest(tvr=tvr):
            with self.assertRaises(ValueError):
                [tv for tv in tvr]

        tvr = TimeValueRange.from_end(10, rate=Fraction(50), inclusivity=TimeValueRange.EXCLUSIVE)
        with self.subTest(tvr=tvr):
            with self.assertRaises(ValueError):
                [tv for tv in tvr]

        tvr = TimeValueRange.eternity()
        with self.subTest(tvr=tvr):
            with self.assertRaises(ValueError):
                [tv for tv in tvr]

        tvr = TimeValueRange.never()
        with self.subTest(tvr=tvr):
            values = [tv for tv in tvr]
            self.assertEqual(values, [])

    def test_reversible(self):
        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.INCLUDE_START)
        with self.subTest(tvr=tvr):
            values = [tv for tv in reversed(tvr)]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in reversed(range(0, 10))])

        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.INCLUSIVE)
        with self.subTest(tvr=tvr):
            values = [tv for tv in reversed(tvr)]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in reversed(range(0, 11))])

        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.EXCLUSIVE)
        with self.subTest(tvr=tvr):
            values = [tv for tv in reversed(tvr)]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in reversed(range(1, 10))])

        tvr = TimeValueRange.from_start_length(0, 10, rate=Fraction(50), inclusivity=TimeValueRange.INCLUDE_END)
        with self.subTest(tvr=tvr):
            values = [tv for tv in reversed(tvr)]
            self.assertEqual(values, [TimeValue(n, rate=Fraction(50)) for n in reversed(range(1, 11))])

        tvr = TimeValueRange.from_str("[0:0_1:0)")
        with self.subTest(tvr=tvr):
            with self.assertRaises(ValueError):
                [tv for tv in reversed(tvr)]

        tvr = TimeValueRange.from_start(0, rate=Fraction(50), inclusivity=TimeValueRange.INCLUSIVE)
        with self.subTest(tvr=tvr):
            with self.assertRaises(ValueError):
                [tv for tv in reversed(tvr)]

        tvr = TimeValueRange.eternity()
        with self.subTest(tvr=tvr):
            with self.assertRaises(ValueError):
                [tv for tv in reversed(tvr)]

        tvr = TimeValueRange.never()
        with self.subTest(tvr=tvr):
            values = [tv for tv in reversed(tvr)]
            self.assertEqual(values, [])

    def test_subranges(self):
        with self.subTest(rate=None):
            tests = [
                (TimeValueRange.from_str("[0_10)@50"), [
                    TimeValueRange.from_str("[{}_{})@50".format(n, n+1)) for n in range(0, 10)
                ]),
                (TimeValueRange.from_str("[0_10]@50"), [
                    TimeValueRange.from_str("[{}_{})@50".format(n, n+1)) for n in range(0, 11)
                ]),
                (TimeValueRange.from_str("(0_10]@50"), [
                    TimeValueRange.from_str("[{}_{})@50".format(n, n+1)) for n in range(1, 11)
                ]),
                (TimeValueRange.from_str("(0_10)@50"), [
                    TimeValueRange.from_str("[{}_{})@50".format(n, n+1)) for n in range(1, 10)
                ]),
                (TimeValueRange.never(), [TimeValueRange.never()]),
                (TimeValueRange.eternity(), [TimeValueRange.eternity()]),
                (TimeValueRange.from_str("[0:0_1:0)"), [TimeValueRange.from_str("[0:0_1:0)")]),
                (TimeValueRange.from_str("_1:0)"), [TimeValueRange.from_str("_1:0)")]),
                (TimeValueRange.from_str("_10)@50"), [TimeValueRange.from_str("_10)@50")]),
            ]

            for (tvr, expected) in tests:
                with self.subTest(tvr=tvr):
                    actual = [tr for tr in tvr.subranges()]
                    self.assertEqual(actual, expected)

        with self.subTest(rate=Fraction(25)):
            tests = [
                (TimeValueRange.from_str("[0_10)@50"), [
                    TimeValueRange.from_str("[{}_{})@50".format(2*n, 2*n+2)) for n in range(0, 5)
                ]),
                (TimeValueRange.from_str("[0_10]@50"), [
                    TimeValueRange.from_str("[{}_{})@50".format(2*n, 2*n+2)) for n in range(0, 5)
                ] + [
                    TimeValueRange.from_str("[10_11)@50")
                ]),
                (TimeValueRange.from_str("(0_10]@50"), [
                    TimeValueRange.from_str("[1_4)@50")
                ] + [
                    TimeValueRange.from_str("[{}_{})@50".format(2*n, 2*n+2)) for n in range(2, 5)
                ] + [
                    TimeValueRange.from_str("[10_11)@50")
                ]),
                (TimeValueRange.from_str("(0_10)@50"), [
                    TimeValueRange.from_str("[1_4)@50")
                ] + [
                    TimeValueRange.from_str("[{}_{})@50".format(2*n, 2*n+2)) for n in range(2, 5)
                ]),
                (TimeValueRange.never(), [TimeValueRange.never()]),
                (TimeValueRange.eternity(), [TimeValueRange.eternity()]),
                (TimeValueRange.from_str("[0:0_0:200000000)"), [
                    TimeValueRange.from_str("[0:{}_0:{})".format(n*40000000, (n+1)*40000000)) for n in range(0, 5)
                ]),
                (TimeValueRange.from_str("[0:0_0:200000000]"), [
                    TimeValueRange.from_str("[0:{}_0:{})".format(n*40000000, (n+1)*40000000)) for n in range(0, 4)
                ] + [
                    TimeValueRange.from_str("[0:160000000_0:200000000]")
                ]),
                (TimeValueRange.from_str("(0:0_0:200000000]"), [
                    TimeValueRange.from_str("(0:0_0:40000000)")
                ] + [
                    TimeValueRange.from_str("[0:{}_0:{})".format(n*40000000, (n+1)*40000000)) for n in range(1, 4)
                ] + [
                    TimeValueRange.from_str("[0:160000000_0:200000000]")
                ]),
                (TimeValueRange.from_str("(0:0_0:200000000)"), [
                    TimeValueRange.from_str("(0:0_0:40000000)")
                ] + [
                    TimeValueRange.from_str("[0:{}_0:{})".format(n*40000000, (n+1)*40000000)) for n in range(1, 5)
                ]),
                (TimeValueRange.from_str("_0:200000000)"), [TimeValueRange.from_str("_0:200000000)")]),
                (TimeValueRange.from_str("_10)@50"), [TimeValueRange.from_str("_10)@50")]),
            ]

            for (tvr, expected) in tests:
                with self.subTest(tvr=tvr):
                    actual = [tr for tr in tvr.subranges(rate=Fraction(25))]
                    self.assertEqual(actual, expected)

    def test_hashable(self):
        tvr1 = TimeValueRange.from_str("()")
        tvr2 = TimeValueRange.from_str("[0:0_1:0)@50")
        self.assertNotEqual(hash(tvr1), hash(tvr2))

    def test_merge_into_ordered_range(self):
        tests = [
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[0_10)@50"),
             [TimeValueRange.from_str("[0_15)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(2, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[3_13)@50"),
             [TimeValueRange.from_str("[0_15)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(2, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[5_7)@50"),
             [TimeValueRange.from_str("[0_7)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(1, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[6_7)@50"),
             [TimeValueRange.from_str("[0_5)@50"), TimeValueRange.from_str("[6_7)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(1, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[0_50)@50"),
             [TimeValueRange.from_str("[0_55)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(6, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(5, 10)],
             TimeValueRange.from_str("[0_10)@50"),
             [TimeValueRange.from_str("[0_10)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(5, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[100_110)@50"),
             [TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)] +
             [TimeValueRange.from_str("[100_110)@50")]),
        ]

        for (ranges, new_range, expected) in tests:
            with self.subTest(ranges=ranges, new_range=new_range):
                actual = list(new_range.merge_into_ordered_ranges(ranges))
                self.assertEqual(actual, expected)

    def test_complement_of_ordered_subranges(self):
        tests = [
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(0, 10)],
             TimeValueRange.from_str("[0_100)@50"),
             [TimeValueRange.from_str("[{}_{})@50".format(n*10 + 5, n*10 + 10)) for n in range(0, 10)]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(1, 9)],
             TimeValueRange.from_str("[0_100)@50"),
             [TimeValueRange.from_str("[0_10)@50")] +
             [TimeValueRange.from_str("[{}_{})@50".format(n*10 + 5, n*10 + 10)) for n in range(1, 8)] +
             [TimeValueRange.from_str("[85_100)@50")]),
            ([TimeValueRange.from_str("[{}_{})@50".format(n*10, n*10 + 5)) for n in range(1, 9)],
             TimeValueRange.from_str("[10_90)@50"),
             [TimeValueRange.from_str("[{}_{})@50".format(n*10 + 5, n*10 + 10)) for n in range(1, 9)]),
        ]

        for (ranges, full_range, expected) in tests:
            with self.subTest(ranges=ranges, full_range=full_range):
                actual = list(full_range.complement_of_ordered_subranges(ranges))
                self.assertEqual(actual, expected)
