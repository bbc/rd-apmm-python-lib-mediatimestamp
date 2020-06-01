# mediatimestamp Changelog

## 2.2.0
- Added the `TimeValue`, `CountRange`, and `TimeValueRange` classes which were previously part of the
  time addressable media api repository. These classes unify a representation of a point in time in terms
  of timestamp and/or a pair of a count and a rate, allowing conversion back and forth between the two
  representations where possible.

## 2.1.0
- Added support for magic methods `__mediatimeoffset__`, `__mediatimestamp__`, and `__mediatimerange__`,
  and associated methods `mediatimeoffset`, `mediatimestamp`, and `mediatimerange` to aid in type conversion.

## 2.0.0
- Dropped all support for python 2.7
- Swapped the mutable and immutable defaults
- Removed the inclusion of the constants at the top level
- Removed all mutable timestamps

## 1.7.3
- Normalise time ranges where start > end to equal TimeRange.never().
- Normalise inclusivity for unbounded time ranges to equal TimeRange.eternity().

## 1.7.2
- This is the final version of this library to support Python 2.7

## 1.7.1
- Correct inclusivity names in `timerange_between` method.

## 1.7.0
- Added extend_to_encompass_timerange function for immutable.TimeRange.
- Hardcode use of python3.4 in RPM spec file to workaround missing python3 soft
link in recent (>3.4.9) centos python34 RPM.

## 1.6.0
- Removed the PRESERVE_START and PRESERVE_END rounding options which are used in TimeRange.normalise().

## 1.5.2
- Fixed bug in taking unions with empty ranges

## 1.5.1
- Fixed bug in `TimeOffset.to_count` (both versions) that caused
  incorrect results when rounding down when the denominator of the
  rate properly divided neither the seconds part nor the nanoseconds
  part of the timestamp, nor the number of nanoseconds in a second,
  but did properly divide the whole timestamp expressed in
  nanoseconds. This bug has been present for some time but had not
  previously been seen because there was no test coverage for
  non-nearest rounding and none of our tests used rates with prime
  denominators other than 2.
- Switched test runner in tox from nose2 to unittest

## 1.5.0
- Added normalisation function for immutable.TimeRange

## 1.4.0
- Added richer comparison functions for immutable.TimeRange

## 1.3.0
- Added at_rate method to immutable.TimeRange which returns an
  iterable of Timestamps

## 1.2.0
- Added new immutable timestamps, offsets, and ranges in their own
namespace
- New style immutable timestamps can be negative
- New style immutable timestamps have a more useful repr

## 1.1.3
- Remove unused custom install command from tox.ini.
- Add Jenkins build trigger to rebuild master every day.
- Allow build to run on a wider variety of slaves.

## 1.1.2
- BUGFIX: upload all pydocs

## 1.1.1
- Added upload of pydoc docs to Jenkinsfile

## 1.1.0
- Added hypothesis submodule containing strategies compatible with the
  `hypothesis` library which can be used to generate timestamps when
  testing code which uses this library.

## 1.0.2
- Updated docstrings to note that "seconds:nanoseconds" is preferred over
  "seconds.fraction".

## 1.0.1
- Added `MAX_NANOSEC` and `MAX_SECONDS` to `TimeOffset`

## 1.0.0
- Initial version, porting timestamp components from nmos-common v.0.6.0
- Has Jenkinsfile for automation
- Has TimeRange
- `TimeOffset.__eq__` doesn't raise exceptions when called with a
  different type
