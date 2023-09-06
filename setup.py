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

from setuptools import setup

# Basic metadata
name = 'mediatimestamp'
description = 'A timestamp library for high precision nanosecond timestamps'
url = 'https://github.com/bbc/rd-apmm-python-lib-mediatimestamp'
author = 'BBC R&D'
author_email = 'cloudfit-opensource@rd.bbc.co.uk'
license = 'Apache 2'
long_description = description


# Execute version file to set version variable
try:
    with open(("{}/_version.py".format(name)), "r") as fp:
        exec(fp.read())
except IOError:
    # Version file doesn't exist, fake it for now
    __version__ = "0.0.0"

package_names = [
    'mediatimestamp',
    'mediatimestamp.hypothesis',
    'mediatimestamp.immutable'
]
packages = {
    pkg: pkg.replace('.', '/') for pkg in package_names
}

# This is where you list packages which are required
packages_required = [
    "python-dateutil>=2.1",
    "deprecated"
]

setup(name=name,
      python_requires='>=3.10.0',
      version=__version__,
      description=description,
      url=url,
      author=author,
      author_email=author_email,
      license=license,
      packages=package_names,
      package_dir=packages,
      package_data={package_name: ['py.typed'] for package_name in package_names},
      install_requires=packages_required,
      scripts=[],
      data_files=[],
      long_description=long_description)
