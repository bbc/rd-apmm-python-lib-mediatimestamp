# mediatimestamp

This library provides nanosecond precision timestamps in python. These
timestamps are intended primarily for use in representing times in TAI
distributed via the PTP protocol (IEEE 1588).

## Instalation

Currently this package is distributed as a wheel and source package on
the BBC R&D APMM artifactory server. Prior to instalation you must set
up your pip environment to access this repository (located at
<https://artifactory.virt.ch.bbc.co.uk/artifactory/api/pypi/ap-python/simple/>
) which requires a forge certificate to access.

To install:

```bash
sudo pip install mediatimestamp
```

## How to set up a development environment

To work on developing this package clone this git repository (which
can always be found at the canonical address:
<git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git>).

The first step after cloning the repository is to run the unit tests
to verify that it works as follows:

```bash
make test
```

The `make test` command invokes `tox`. You can invoke it directly like
this:

```bash
    tox
```

either way it makes use of the configuration in `tox.ini` to set up
virtual environments to run tests in and then run all tests. The
provided configuration runs the `nose2` test runner under `python2.7`
and `python3`, but other configurations are possible.

The default test command is:

```bash
    nose2 --with-coverage --coverage-report=annotate \
        --coverage-report=term --coverage=mediatimestamp
```

which will discover all tests in the `tests` directory and run them
recording coverage of files in the main package directory. The
coverage report is printed to the terminal during running but is also
used to create annotated `.py,cover` files which are copies of the
`.py` source files with each line marked with a character to indicate
whether it is covered (`>`), not covered (`!`), or specifically
ignored for coverage purposes (`-`).

Once you've run the tests it will have created tox virtual
environments with the package installed. If you activate these
environments, eg. with:

```bash
. .tox/py3/bin/activate
```

then you will be in a python environment where your package is already
installed *and* any changes you make to the source code in place will
automatically be used by python.

To leave this environment type:

```bash
deactivate
```

## Debian and RPM Packaging

Debian and RPM packages can be built using:

```bash
make deb
```

and

```bash
make rpm
```

## Contributing

The code in this repository was previously released as part of the
nmos-common library (<https://github.com/bbc/nmos-common/>). For
contributing wok please see the file [CONTRIBUTING.md](./CONTRIBUTING.md) in this repository.
