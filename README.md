# mediatimestamp

Nanosecond precision timestamps for python.

## Introduction

This library provides nanosecond precision timestamps in python. These
timestamps are intended primarily for use in representing times in TAI
distributed via the PTP protocol (IEEE 1588).

## Installation

### Requirements

* A working Python 2.7 or Python 3.x installation
* BBC R&D's internal deb repository set up as a source for apt (if installing via apt-get)
* The tool [tox](https://tox.readthedocs.io/en/latest/) is needed to run the unittests, but not required to use the library.

### Steps

```bash
# Install from pip
$ pip install mediatimestamp

# Install via apt-get
$ apt-get install python-mediatimestamp python3-mediatimestamp

# Install directly from source repo
$ git clone git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git
$ cd rd-apmm-python-lib-mediatimestamp
$ pip install -e .
```

## Usage

```python
from mediatimestamp.immutable import Timestamp

# Print the current time in seconds:nanoseconds format
print(Timestamp.get_time())
```

This module provides two different interfaces
`mediatimestamp.immutable` and `mediatimestamp.mutable`, each of which
contains three main classes which are used for representing time:

* `Timestamp` represents an instant in time expressed as a nanosecond
   precision timestamp.
* `TimeOffset` represents a duration measured in nanoseconds.
* `TimeRange` represents a time range defined by its start and end
  timestamps, which may be inclusive of neither, one, or both of its
  ends.

For backwards compatibility reasons the `mutable` versions of these
classes can also be imported directly from the base level of
`mediatimestamp`. It is recommended that all future code not use this
method but instead use the `mediatimestamp.immutable` submodule. In
most cases this will not require much change to existing code. In a
future version of this code the version imported from the base level may
change, though this will not happen without a major version bump. It is
intended that the immutable version will always be available via the
`mediatimestamp.immutable` module even if this change is made.

In addition a submodule `mediatimestamp.hypothesis.strategies` is
provided for those who wish to make use of these timestamps in code
that is to be tested using the `hypothesis` library. The strategies
provided in this module allow the creation of hypothesis based tests
which make use of `Timestamp` and `TimeRange` objects. Versions
generating mutable and immutable timestamps are provided.

## Documentation

The API is well documented in the docstrings of the module mediatimestamp, to view:

```bash
pydoc mediatimestamp
```

## Development
### Testing

To run the unittests for this package in a virtual environment follow these steps:

```bash
$ git clone git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git
$ cd rd-apmm-python-lib-mediatimestamp
$ make test
```
### Packaging

Debian and RPM packages can be built using:

```bash
# Debian packaging
$ make deb

# RPM packageing
$ make rpm
```

### Continuous Integration

This repository includes a Jenkinsfile which makes use of custom steps defined in a BBC internal
library for use on our own Jenkins instances. As such it will not be immediately useable outside
of a BBC environment, but may still serve as inspiration and an example of how to implement CI
for this package.

## Versioning

We use [Semantic Versioning](https://semver.org/) for this repository

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## Contributing

The code in this repository was previously released as part of the
nmos-common library (<https://github.com/bbc/nmos-common/>). For
contributing wok please see the file [CONTRIBUTING.md](./CONTRIBUTING.md) in this repository.

Please ensure you have run the test suite before submitting a Pull Request, and include a version bump in line with our [Versioning](#versioning) policy.

## Authors

* James Weaver (james.barrett@bbc.co.uk)
* Philip deNier (philip.denier@bbc.co.uk)
* Sam Nicholson (sam.nicholson@bbc.co.uk)
* James Sandford (james.sandford@bbc.co.uk
* Alex Rawcliffe (alex.rawcliffe@bbc.co.uk)

## License

See [LICENSE.md](LICENSE.md)
