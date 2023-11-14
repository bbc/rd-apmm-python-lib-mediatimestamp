# mediatimestamp

Nanosecond precision timestamps for python.

## Introduction

This library provides nanosecond precision timestamps in python. These
timestamps are intended primarily for use in representing times in TAI
distributed via the PTP protocol (IEEE 1588).

## Installation

### Requirements

* A working Python 3.10+ installation
* The tool [Docker](https://docs.docker.com/engine/install/) is needed to run the tests, but not required to use the library.

### Steps

```bash
# Install from pip
$ pip install mediatimestamp

# Install directly from source repo
$ git clone git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git
$ cd rd-apmm-python-lib-mediatimestamp
$ make install
```

## Usage

```python
from mediatimestamp.immutable import Timestamp

# Print the current time in seconds:nanoseconds format
print(Timestamp.get_time())
```

This module provides three main classes which are used for representing
time:

* `Timestamp` represents an instant in time expressed as a nanosecond
   precision timestamp.
* `TimeRange` represents a time range defined by its start and end
  timestamps, which may be inclusive of neither, one, or both of its
  ends.

For backwards compatibility reasons the classes can be imported either
directly from the base level of `mediatimestamp` or as
`mediatimestamp.immutable`.

In addition a submodule `mediatimestamp.hypothesis.strategies` is
provided for those who wish to make use of these timestamps in code
that is to be tested using the `hypothesis` library. The strategies
provided in this module allow the creation of hypothesis based tests
which make use of `Timestamp` and `TimeRange` objects.

## Documentation

The API is well documented in the docstrings of the module mediatimestamp, to view:

```bash
make docs
```
This command will render documentation as HTML in the `/docs` directory.

A rendered version of this documentation is available [here](https://bbc.github.io/rd-apmm-python-lib-mediatimestamp/mediatimestamp/mediatimestamp.html).

## Development
### Commontooling

This repository uses a library of makefiles, templates, and other tools for development tooling and CI workflows. To discover operations that may be run against this repo, run the following in the top level of the repo:

```bash
$ make
```

### Testing

To run the unittests for this package in a docker container follow these steps:

```bash
$ git clone git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git
$ cd rd-apmm-python-lib-mediatimestamp
$ make test
```

### Continuous Integration

This repository includes [GitHub Actions workflows](./.github/workflows/) for CI.
The shared workflows are centrally managed and should not be modified.

## Versioning

We use [Semantic Versioning](https://semver.org/) for this repository

## Contributing

The code in this repository was previously released as part of the
nmos-common library (<https://github.com/bbc/nmos-common/>). For
contributing work please see the file [CONTRIBUTING.md](./CONTRIBUTING.md) in this repository.

Please ensure you have run the test suite before submitting a Pull Request, and include a version bump in line with our [Versioning](#versioning) policy.

## Authors

* James Weaver
* Philip deNier
* Sam Nicholson
* James Sandford
* Alex Rawcliffe

For further information, contact <cloudfit-opensource@rd.bbc.co.uk>

## License

See [LICENSE.md](LICENSE.md)
