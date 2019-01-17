# mediatimestamp Changelog

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
