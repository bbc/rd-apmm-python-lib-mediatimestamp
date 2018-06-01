# mediatimestamp

This library provides nanosecond precision timestamps in python. These
timestamps are intended primarily for use in representing times in TAI
distributed via the PTP protocol (IEEE 1588).

## Testing

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

## Debian and RPM Packaging

Debian and RPM packages can be built using:

```bash
make deb
```

and

```bash
make rpm
```



THIS IS A DUMMY COMMIT TO CHECK CI
j.hdvk;jldh
,jhfljkdhf;djhf
hjkdljkhgfdlkj;uhf;iu
;lfivhpioehfgrp;
vldkhk;hsk
kjhdhkludklhdjhdjk
kujhdkluhshlkus
