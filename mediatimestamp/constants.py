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

# THESE CONSTANTS ARE NOT PART OF THIS LIBRARY'S PUBLIC INTERFACE
# The same values are made available by methods that are, such as
#
# Timestamp.MAX_NANOSEC
#
# So use those instead. At some point these constants could go away without warning

MAX_NANOSEC = 1000000000
MAX_SECONDS = 281474976710656

# The UTC leap seconds table below was extracted from the information provided at
# http://www.ietf.org/timezones/data/leap-seconds.list
#
# The order has been reversed.
# The NTP epoch seconds have been converted to Unix epoch seconds. The difference between
# the NTP epoch at 1 Jan 1900 and the Unix epoch at 1 Jan 1970 is 2208988800 seconds

UTC_LEAP = [
  # || UTC SEC  |  TAI SEC - 1 ||
  (1483228800, 1483228836),    # 1 Jan 2017, 37 leap seconds
  (1435708800, 1435708835),    # 1 Jul 2015, 36 leap seconds
  (1341100800, 1341100834),    # 1 Jul 2012, 35 leap seconds
  (1230768000, 1230768033),    # 1 Jan 2009, 34 leap seconds
  (1136073600, 1136073632),    # 1 Jan 2006, 33 leap seconds
  (915148800,  915148831),     # 1 Jan 1999, 32 leap seconds
  (867715200,  867715230),     # 1 Jul 1997, 31 leap seconds
  (820454400,  820454429),     # 1 Jan 1996, 30 leap seconds
  (773020800,  773020828),     # 1 Jul 1994, 29 leap seconds
  (741484800,  741484827),     # 1 Jul 1993, 28 leap seconds
  (709948800,  709948826),     # 1 Jul 1992, 27 leap seconds
  (662688000,  662688025),     # 1 Jan 1991, 26 leap seconds
  (631152000,  631152024),     # 1 Jan 1990, 25 leap seconds
  (567993600,  567993623),     # 1 Jan 1988, 24 leap seconds
  (489024000,  489024022),     # 1 Jul 1985, 23 leap seconds
  (425865600,  425865621),     # 1 Jul 1983, 22 leap seconds
  (394329600,  394329620),     # 1 Jul 1982, 21 leap seconds
  (362793600,  362793619),     # 1 Jul 1981, 20 leap seconds
  (315532800,  315532818),     # 1 Jan 1980, 19 leap seconds
  (283996800,  283996817),     # 1 Jan 1979, 18 leap seconds
  (252460800,  252460816),     # 1 Jan 1978, 17 leap seconds
  (220924800,  220924815),     # 1 Jan 1977, 16 leap seconds
  (189302400,  189302414),     # 1 Jan 1976, 15 leap seconds
  (157766400,  157766413),     # 1 Jan 1975, 14 leap seconds
  (126230400,  126230412),     # 1 Jan 1974, 13 leap seconds
  (94694400,   94694411),      # 1 Jan 1973, 12 leap seconds
  (78796800,   78796810),      # 1 Jul 1972, 11 leap seconds
  (63072000,   63072009),      # 1 Jan 1972, 10 leap seconds
]
