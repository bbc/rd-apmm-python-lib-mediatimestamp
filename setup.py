# Copyright 2017 British Broadcasting Corporation
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

from __future__ import print_function
from setuptools import setup
import os

# Basic metadata
name = 'mediatimestamp'
version = '2.2.0'
description = 'A timestamp library for high precision nanosecond timestamps'
url = 'https://github.com/bbc/rd-apmm-python-lib-mediatimestamp'
author = 'James P. Weaver'
author_email = 'james.barrett@bbc.co.uk'
license = 'Apache 2'
long_description = description


def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )


def find_packages(path, base=""):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package(dir):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages


packages = find_packages(".")
package_names = packages.keys()

# This is where you list packages which are required
packages_required = [
    "python-dateutil>=2.1,<2.8.1"
]

# This is where you list locations for packages not
# available from pip. Each entry must be of the form:
#  <url>#egg=<pkgname>=<version>
# eg. https://github.com/bbc/rd-apmm-python-lib-nmos-common#egg=nmoscommon=0.1.0
deps_required = []

setup(name=name,
      python_requires='>=3.6.0',
      version=version,
      description=description,
      url=url,
      author=author,
      author_email=author_email,
      license=license,
      packages=package_names,
      package_dir=packages,
      package_data={name: ['py.typed'] for name in package_names},
      install_requires=packages_required,
      scripts=[],
      data_files=[],
      long_description=long_description)
