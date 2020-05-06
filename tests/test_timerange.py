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

from fractions import Fraction

from mediatimestamp.immutable import (
    Timestamp,
    TimeOffset,
    TsValueError,
    TimeRange,
    SupportsMediaTimeRange,
    mediatimerange)


class TestTimeRange (unittest.TestCase):
    def test_mediatimerange(self):
        tr = TimeRange.never()
        self.assertIsInstance(tr, SupportsMediaTimeRange)

        ts = Timestamp()
        self.assertIsInstance(ts, SupportsMediaTimeRange)

        self.assertEqual(tr, mediatimerange(tr))
        self.assertEqual(TimeRange.from_single_timestamp(ts), mediatimerange(ts))

        class _convertible(object):
            def __mediatimerange__(self) -> TimeRange:
                return TimeRange.eternity()

        c = _convertible()
        self.assertIsInstance(c, SupportsMediaTimeRange)
        self.assertEqual(TimeRange.eternity(), mediatimerange(c))

        class _ts_convertible (object):
            def __mediatimestamp__(self) -> Timestamp:
                return Timestamp()

        tsc = _ts_convertible()

        self.assertIsInstance(tsc, SupportsMediaTimeRange)
        self.assertEqual(TimeRange.from_single_timestamp(Timestamp()), mediatimerange(tsc))

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

        self.assertTrue(TimeRange(a, c, TimeRange.INCLUSIVE).contains_subrange(b))

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

        self.assertEqual(TimeRange(a, c, TimeRange.INCLUDE_START).intersect_with(b), mediatimerange(b))

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
            (TimeRange.from_str("[10:0_11:0)"), Fraction(50, 1), TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 50, 1) for n in range(0, 50)]),
            (TimeRange.from_str("[10:0_11:0)"), Fraction(50, 2), TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 25, 1) for n in range(0, 25)]),
            (TimeRange.from_str("[10:0_11:0)"), Fraction(25, 2), TimeOffset(),
             [Timestamp(10, 0) + TimeOffset.from_count(n, 25, 2) for n in range(0, 13)]),
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

    def test_never_normalise(self):
        """Check 'never' (empty) normalisation"""
        test_data = [
            TimeRange.from_str("[100:0_0:0]"),
            TimeRange.from_str("[10:0_10:0)"),
            TimeRange.from_str("(10:0_10:0]"),
        ]

        for tr in test_data:
            with self.subTest(tr=tr):
                self.assertEqual(tr.start, TimeRange.never().start)
                self.assertEqual(tr.end, TimeRange.never().end)
                self.assertEqual(tr.inclusivity, TimeRange.never().inclusivity)

    def test_eternity_normalise(self):
        """Check 'eternity' normalisation"""
        tr = TimeRange(None, None, TimeRange.EXCLUSIVE)
        self.assertEqual(tr.inclusivity, TimeRange.INCLUSIVE)
