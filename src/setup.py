# coding: utf-8
# Copyright © 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from setuptools import setup, find_packages

NAME = "esm"
VERSION = "0.8.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools


# XXX update if requirements.txt content is changed
REQUIRES = [
    'connexion',
    'python_dateutil',
    'setuptools',
    'pymongo',
    'docker-compose',
    'docker',
    'pykube',
    'healthcheck',
    'tornado',
    'pykafka',
    'epm-client',
    'orator',
    'pymysql',
    'keystonemiddleware',
    'python-memcached',
    'jsonpickle',
    'kafka',
    'requests',
]

DEP_LINKS = [
    "git+https://github.com/mpauls/epm-client-python.git"
]

setup(
    name=NAME,
    version=VERSION,
    description="ElasTest Service Manager API",
    author_email="elastest-users@googlegroups.com",
    url="https://github.com/elastest/bugtracker",
    keywords=["Swagger", "ElasTest Service Manager API", "OSBA", "Serivce", "Delivery"],
    install_requires=REQUIRES,
    dependency_links=DEP_LINKS,
    packages=find_packages(),
    package_data={'': ['esm/swagger/swagger.yaml']},
    include_package_data=True,
    long_description="""\
    This is the service manager API. It is an extension of the the Open Service Broker API. The Open Service Broker 
    API defines the contract between the a requesting client and the service broker. The broker is expected to 
    implement several HTTP (or HTTPS) endpoints underneath a URI prefix. One or more services can be provided by a 
    single broker, and load balancing enables horizontal scalability of redundant brokers. Multiple service provider 
    instances can be supported by a single broker using different URL prefixes and credentials. [Learn more about 
    the Service Broker API.] (https://github.com/openservicebrokerapi/servicebroker/). Note the [topic on orphan reso
    lution](https://github.com/openservicebrokerapi/servicebroker/blob/master/_spec.md#orphans). It is not 
    dealt with in this spec. 
    """
)
