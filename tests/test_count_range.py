# Copyright 2019 British Broadcasting Corporation
#
# This is an internal BBC tool and is not licensed externally
# If you have received a copy of this erroneously then you do
# not have permission to reproduce it.

import unittest

from mediatimestamp import CountRange


class TestCountRange(unittest.TestCase):
    def test_never(self):
        rng = CountRange.never()

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(1, rng)

        self.assertTrue(rng.is_empty())
        self.assertEqual(rng.to_str(), "()")

    def test_eternity(self):
        alltime = CountRange.eternity()

        self.assertIn(-1, alltime)
        self.assertIn(0, alltime)
        self.assertIn(1, alltime)

        self.assertEqual(alltime.to_str(), "_")

    def test_bounded_on_right_inclusive(self):
        rng = CountRange.from_end(100)

        self.assertIn(-1, rng)
        self.assertIn(0, rng)
        self.assertIn(99, rng)
        self.assertIn(100, rng)
        self.assertNotIn(101, rng)

        self.assertEqual(rng.to_str(), "_101)")

    def test_bounded_on_right_exclusive(self):
        rng = CountRange.from_end(100, inclusivity=CountRange.EXCLUSIVE)

        self.assertIn(-1, rng)
        self.assertIn(0, rng)
        self.assertIn(99, rng)
        self.assertNotIn(100, rng)
        self.assertNotIn(101, rng)

        self.assertEqual(rng.to_str(), "_100)")

    def test_bounded_on_left_inclusive(self):
        rng = CountRange.from_start(100)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertIn(100, rng)
        self.assertIn(101, rng)

        self.assertEqual(rng.to_str(), "[100_")

    def test_bounded_on_left_exclusive(self):
        rng = CountRange.from_start(100, inclusivity=CountRange.EXCLUSIVE)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertNotIn(100, rng)
        self.assertIn(101, rng)

        self.assertEqual(rng.to_str(), "[101_")

    def test_bounded_inclusive(self):
        rng = CountRange(100, 200)

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
        rng = CountRange(100, 200, inclusivity=CountRange.EXCLUSIVE)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertNotIn(100, rng)
        self.assertIn(101, rng)
        self.assertIn(199, rng)
        self.assertNotIn(200, rng)
        self.assertNotIn(201, rng)

        self.assertEqual(rng.to_str(), "[101_200)")

    def test_single_tv(self):
        rng = CountRange.from_single_count(100)

        self.assertNotIn(-1, rng)
        self.assertNotIn(0, rng)
        self.assertNotIn(99, rng)
        self.assertIn(100, rng)
        self.assertNotIn(101, rng)

        self.assertEqual(rng.to_str(), "[100_101)")

    def test_from_str(self):
        tests = [
            ("()", CountRange.never()),
            ("[]", CountRange.never()),
            ("", CountRange.never()),
            ("_", CountRange.eternity()),
            ("_200", CountRange.from_end(200)),
            ("[_200]", CountRange.from_end(200, inclusivity=CountRange.INCLUSIVE)),
            ("(_200)", CountRange.from_end(200, inclusivity=CountRange.EXCLUSIVE)),
            ("100_", CountRange.from_start(100)),
            ("[100_]", CountRange.from_start(100, inclusivity=CountRange.INCLUSIVE)),
            ("(100_)", CountRange.from_start(100, inclusivity=CountRange.EXCLUSIVE)),
            ("100_200", CountRange(100, 200)),
            ("[100_200]", CountRange(100, 200, inclusivity=CountRange.INCLUSIVE)),
            ("(100_200)", CountRange(100, 200, inclusivity=CountRange.EXCLUSIVE)),
            ("(100_200]", CountRange(100, 200, inclusivity=CountRange.INCLUDE_END)),
            ("[100_200)", CountRange(100, 200, inclusivity=CountRange.INCLUDE_START)),
            ("200", CountRange.from_single_count(200)),
        ]

        for (s, tr) in tests:
            self.assertEqual(tr, CountRange.from_str(s))

    def test_subrange(self):
        a = 50
        b = 100
        c = 200
        d = 250

        self.assertTrue(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(a, b, inclusivity=CountRange.INCLUSIVE)))
        self.assertFalse(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(a, b, inclusivity=CountRange.INCLUSIVE)))
        self.assertTrue(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(a, b, inclusivity=CountRange.EXCLUSIVE)))
        self.assertTrue(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(a, b, inclusivity=CountRange.EXCLUSIVE)))

        self.assertTrue(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)))
        self.assertFalse(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)))
        self.assertTrue(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.EXCLUSIVE)))
        self.assertTrue(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.EXCLUSIVE)))

        self.assertTrue(CountRange(a, d, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)))
        self.assertTrue(CountRange(a, d, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)))
        self.assertTrue(CountRange(a, d, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.EXCLUSIVE)))
        self.assertTrue(CountRange(a, d, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(b, c, inclusivity=CountRange.EXCLUSIVE)))

        self.assertFalse(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(b, d, inclusivity=CountRange.INCLUSIVE)))
        self.assertFalse(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(b, d, inclusivity=CountRange.INCLUSIVE)))
        self.assertFalse(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).contains_subrange(
            CountRange(b, d, inclusivity=CountRange.EXCLUSIVE)))
        self.assertFalse(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).contains_subrange(
            CountRange(b, d, inclusivity=CountRange.EXCLUSIVE)))

    def test_intersection(self):
        a = 50
        b = 100
        c = 200
        d = 250

        self.assertEqual(CountRange(a, b, inclusivity=CountRange.INCLUSIVE).intersect_with(
                            CountRange(c, d, inclusivity=CountRange.INCLUSIVE)),
                         CountRange.never())

        self.assertEqual(CountRange(a, b, inclusivity=CountRange.INCLUSIVE).intersect_with(
                            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)),
                         CountRange.from_single_count(b))

        self.assertEqual(CountRange(a, b, inclusivity=CountRange.EXCLUSIVE).intersect_with(
                            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)),
                         CountRange.never())

        self.assertEqual(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).intersect_with(
                            CountRange(b, d, inclusivity=CountRange.INCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.INCLUSIVE))

        self.assertEqual(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).intersect_with(
                            CountRange(b, d, inclusivity=CountRange.INCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.INCLUDE_START))

        self.assertEqual(CountRange(a, c, inclusivity=CountRange.INCLUSIVE).intersect_with(
                            CountRange(b, d, inclusivity=CountRange.EXCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.INCLUDE_END))

        self.assertEqual(CountRange(a, c, inclusivity=CountRange.EXCLUSIVE).intersect_with(
                            CountRange(b, d, inclusivity=CountRange.EXCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.EXCLUSIVE))

        self.assertEqual(CountRange(a, d, inclusivity=CountRange.INCLUSIVE).intersect_with(
                            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.INCLUSIVE))

        self.assertEqual(CountRange(a, d, inclusivity=CountRange.EXCLUSIVE).intersect_with(
                            CountRange(b, c, inclusivity=CountRange.INCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.INCLUSIVE))

        self.assertEqual(CountRange(a, d, inclusivity=CountRange.INCLUSIVE).intersect_with(
                            CountRange(b, c, inclusivity=CountRange.EXCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.EXCLUSIVE))

        self.assertEqual(CountRange(a, d, inclusivity=CountRange.EXCLUSIVE).intersect_with(
                            CountRange(b, c, inclusivity=CountRange.EXCLUSIVE)),
                         CountRange(b, c, inclusivity=CountRange.EXCLUSIVE))

        self.assertEqual(CountRange.eternity().intersect_with(
                            CountRange(a, b, inclusivity=CountRange.INCLUSIVE)),
                         CountRange(a, b, inclusivity=CountRange.INCLUSIVE))

        self.assertEqual(CountRange.eternity().intersect_with(
                            CountRange(a, b, inclusivity=CountRange.EXCLUSIVE)),
                         CountRange(a, b, inclusivity=CountRange.EXCLUSIVE))

        self.assertEqual(CountRange.never().intersect_with(
                            CountRange(a, b, inclusivity=CountRange.INCLUSIVE)),
                         CountRange.never())

        self.assertEqual(CountRange.never().intersect_with(
                            CountRange(a, b, inclusivity=CountRange.EXCLUSIVE)),
                         CountRange.never())

        self.assertEqual(CountRange.never().intersect_with(
                            CountRange.eternity()),
                         CountRange.never())

    def test_length(self):
        a = 50
        b = 100
        c = 200

        rng = CountRange(a, b, inclusivity=CountRange.INCLUSIVE)
        self.assertEqual(rng.length, b - a + 1)

        rng = CountRange(None, b, inclusivity=CountRange.INCLUSIVE)
        self.assertEqual(rng.length, float("inf"))

        rng = CountRange(a, None, inclusivity=CountRange.INCLUSIVE)
        self.assertEqual(rng.length, float("inf"))

        rng = CountRange(None, None, inclusivity=CountRange.INCLUSIVE)
        self.assertEqual(rng.length, float("inf"))

        rng = CountRange(a, b, inclusivity=CountRange.INCLUSIVE)
        with self.assertRaises(ValueError):
            rng.length = (c - a)
        self.assertEqual(rng, CountRange(a, b, inclusivity=CountRange.INCLUSIVE))

        rng = CountRange(None, None, inclusivity=CountRange.INCLUSIVE)
        with self.assertRaises(ValueError):
            rng.length = (b - a)

        rng = CountRange(a, b, inclusivity=CountRange.INCLUSIVE)
        with self.assertRaises(ValueError):
            rng.length = (a - c)

    def test_repr(self):
        """This tests that the repr function turns time ranges into `eval`-able strings."""
        test_trs = [
            (CountRange.from_str("(100_200)"), "mediatimestamp.count_range.CountRange.from_str('[101_200)')"),
            (CountRange.from_str("[100_200]"), "mediatimestamp.count_range.CountRange.from_str('[100_201)')"),
            (CountRange.from_str("[100_"), "mediatimestamp.count_range.CountRange.from_str('[100_')")
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
            (CountRange.from_str("_"), CountRange.from_str("_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (CountRange.from_str("_"), CountRange.from_str("[0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (CountRange.from_str("_"), CountRange.from_str("_0]"),
             (True, False, False, False, False, False, False, True, True, True)),
            (CountRange.from_str("_"), CountRange.from_str("[0_10)"),
             (False, False, False, False, True, False, False, True, True, True)),

            (CountRange.from_str("_5)"), CountRange.from_str("_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("_5)"), CountRange.from_str("[0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (CountRange.from_str("_5)"), CountRange.from_str("_0]"),
             (True, False, False, False, False, False, False, True, True, True)),
            (CountRange.from_str("_5)"), CountRange.from_str("_10]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("_5)"), CountRange.from_str("[0_10)"),
             (False, True, False, False, True, False, True, False, True, True)),

            (CountRange.from_str("_0)"), CountRange.from_str("_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("_0)"), CountRange.from_str("[0_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (CountRange.from_str("_0)"), CountRange.from_str("_0]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("_0)"), CountRange.from_str("_0)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (CountRange.from_str("_0)"), CountRange.from_str("_10]"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("_0)"), CountRange.from_str("[0_10)"),
             (False, False, True, False, True, False, True, False, False, True)),
            (CountRange.from_str("_0)"), CountRange.from_str("(0_10)"),
             (False, False, True, False, True, False, True, False, False, False)),
            (CountRange.from_str("_0)"), CountRange.from_str("[5_10)"),
             (False, False, True, False, True, False, True, False, False, False)),

            (CountRange.from_str("[0_)"), CountRange.from_str("_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("[0_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("(0_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("[5_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("_0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("_10]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("[0_10)"),
             (True, False, False, False, False, False, False, True, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("(0_10)"),
             (False, False, False, False, True, False, False, True, True, True)),
            (CountRange.from_str("[0_)"), CountRange.from_str("[5_10)"),
             (False, False, False, False, True, False, False, True, True, True)),

            (CountRange.from_str("[5_)"), CountRange.from_str("_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("[0_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("(0_"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("[5_"),
             (True, True, False, False, False, False, False, False, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("(5_"),
             (False, True, False, False, True, False, False, False, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("_0]"),
             (False, False, False, True, False, True, False, True, False, False)),
            (CountRange.from_str("[5_)"), CountRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, False)),
            (CountRange.from_str("[5_)"), CountRange.from_str("_10]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("[0_10)"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("(0_10)"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[5_)"), CountRange.from_str("[5_10)"),
             (True, False, False, False, False, False, False, True, True, True)),

            (CountRange.from_str("[0_10)"), CountRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("(0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[10_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("(10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("_0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("_10]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("_10)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[0_10)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("(0_10)"),
             (False, True, False, False, True, False, False, False, True, True)),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[5_10)"),
             (False, True, False, False, True, False, False, False, True, True)),

            (CountRange.from_str("(0_10)"), CountRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("[0_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("(0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("[10_"),
             (False, False, True, False, True, False, True, False, False, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("(10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("_0]"),
             (False, False, False, True, False, True, False, True, False, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, False)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("_10]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("_10)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("[0_10)"),
             (True, True, False, False, False, True, False, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("(0_10)"),
             (True, True, False, False, False, False, False, False, True, True)),
            (CountRange.from_str("(0_10)"), CountRange.from_str("[5_10)"),
             (False, True, False, False, True, False, False, False, True, True)),

            (CountRange.from_str("[0_5)"), CountRange.from_str("_"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("[0_"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("(0_"),
             (False, True, False, False, True, False, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("[10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("(10_"),
             (False, False, True, False, True, False, True, False, False, False)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("_0]"),
             (True, False, False, False, False, True, False, True, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("_0)"),
             (False, False, False, True, False, True, False, True, False, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("_10]"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("_10)"),
             (True, True, False, False, False, True, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("[0_10)"),
             (True, True, False, False, False, False, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("(0_10)"),
             (False, True, False, False, True, False, True, False, True, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("[5_10)"),
             (False, False, True, False, True, False, True, False, False, True)),
            (CountRange.from_str("[0_5)"), CountRange.from_str("(5_10)"),
             (False, False, True, False, True, False, True, False, False, False)),

            (CountRange.never(), CountRange.from_str("_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("[0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("(0_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("[10_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("(10_"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("_0]"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("_0)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("_10]"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("[0_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("(0_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("[5_10)"),
             (False, False, False, False, False, False, False, False, True, True)),
            (CountRange.never(), CountRange.from_str("(5_10)"),
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
            (CountRange.from_str("_"), 0,
             CountRange.from_str("_0)"), CountRange.from_str("[0_")),
            (CountRange.from_str("[0_"), 10,
             CountRange.from_str("[0_10)"), CountRange.from_str("[10_")),
            (CountRange.from_str("_10)"), 0,
             CountRange.from_str("_0)"), CountRange.from_str("[0_10)")),
            (CountRange.from_str("[0_10)"), 5,
             CountRange.from_str("[0_5)"), CountRange.from_str("[5_10)")),
            (CountRange.from_str("[0_10]"), 5,
             CountRange.from_str("[0_5)"), CountRange.from_str("[5_10]")),
            (CountRange.from_str("(0_10)"), 5,
             CountRange.from_str("(0_5)"), CountRange.from_str("[5_10)")),
            (CountRange.from_str("(0_10]"), 5,
             CountRange.from_str("(0_5)"), CountRange.from_str("[5_10]")),
            (CountRange.from_str("[0]"), 0,
             CountRange.never(), CountRange.from_str("[0_0]")),
            (CountRange.from_str("[0_10)"), 0,
             CountRange.never(), CountRange.from_str("[0_10)")),
            (CountRange.from_str("[0_10]"), 10,
             CountRange.from_str("[0_10)"), CountRange.from_str("[10]")),
        ]

        for (tr, ts, left, right) in test_data:
            with self.subTest(tr=tr, ts=ts, expected=(left, right)):
                self.assertEqual(tr.split_at(ts), (left, right))

        test_data = [
            (CountRange.from_str("[0_10)"), 11),
            (CountRange.from_str("[0_10)"), 10),
        ]

        for (tr, ts) in test_data:
            with self.subTest(tr=tr, ts=ts):
                with self.assertRaises(ValueError):
                    tr.split_at(ts)

    def test_extend_to_encompass(self):
        test_data = [
            (CountRange.from_str("()"), CountRange.from_str("()"),
             CountRange.from_str("()")),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[10]"),
             CountRange.from_str("[0_10]")),
            (CountRange.from_str("_"), CountRange.from_str("[0]"),
             CountRange.from_str("_")),
            (CountRange.from_str("_"), CountRange.from_str("()"),
             CountRange.from_str("_")),
            (CountRange.from_str("()"), CountRange.from_str("_"),
             CountRange.from_str("_")),
            (CountRange.from_str("_10)"), CountRange.from_str("[0_"),
             CountRange.from_str("_")),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[5_"),
             CountRange.from_str("[0_")),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[5_15)"),
             CountRange.from_str("[0_15)")),
            (CountRange.from_str("[0_10)"), CountRange.from_str("[10_15)"),
             CountRange.from_str("[0_15)")),
            (CountRange.from_str("()"), CountRange.from_str("[5_"),
             CountRange.from_str("[5_")),
            (CountRange.from_str("()"), CountRange.from_str("[5_15)"),
             CountRange.from_str("[5_15)")),
            (CountRange.from_str("()"), CountRange.from_str("_15)"),
             CountRange.from_str("_15)")),

            # discontiguous
            (CountRange.from_str("_0)"), CountRange.from_str("(0_"),
             CountRange.from_str("_")),
            (CountRange.from_str("(0_"), CountRange.from_str("_0)"),
             CountRange.from_str("_")),
            (CountRange.from_str("[0_5)"), CountRange.from_str("(5_15)"),
             CountRange.from_str("[0_15)")),
            (CountRange.from_str("(5_15)"), CountRange.from_str("[0_5)"),
             CountRange.from_str("[0_15)")),
            (CountRange.from_str("[0_5)"), CountRange.from_str("[10_15)"),
             CountRange.from_str("[0_15)")),
            (CountRange.from_str("[10_15)"), CountRange.from_str("[0_5)"),
             CountRange.from_str("[0_15)")),
        ]

        for (first, second, expected) in test_data:
            with self.subTest(first=first, second=second, expected=expected):
                self.assertEqual(first.extend_to_encompass_range(second), expected)

    def test_union_raises(self):
        # discontiguous part of test_extend_to_encompass raises for a union
        test_data = [
            (CountRange.from_str("_0)"), CountRange.from_str("(0_")),
            (CountRange.from_str("(0_"), CountRange.from_str("_0)")),
            (CountRange.from_str("[0_5)"), CountRange.from_str("(5_15)")),
            (CountRange.from_str("(5_15)"), CountRange.from_str("[0_5)")),
            (CountRange.from_str("[0_5)"), CountRange.from_str("[10_15)")),
            (CountRange.from_str("[10_15)"), CountRange.from_str("[0_5)")),
        ]

        for (first, second) in test_data:
            with self.subTest(first=first, second=second):
                with self.assertRaises(ValueError):
                    first.union_with_range(second)

    def test_immutable(self):
        cr = CountRange(0, 1)
        with self.assertRaises(ValueError):
            cr._start = 1

        with self.assertRaises(ValueError):
            cr._end = 1

        with self.assertRaises(ValueError):
            cr._inclusivity = CountRange.INCLUSIVE
