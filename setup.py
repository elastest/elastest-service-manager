# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "esm"
VERSION = "0.1.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="ElasTest Service Manager API",
    author_email="elastest-users@googlegroups.com",
    url="https://github.com/elastest/bugtracker",
    keywords=["Swagger", "ElasTest Service Manager API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    long_description="""\
    This is the service manager API. It is an extension of the the Open Service Broker API. The Open Service Broker API defines the contract between the a requesting client and the service broker. The broker is expected to implement several HTTP (or HTTPS) endpoints underneath a URI prefix. One or more services can be provided by a single broker, and load balancing enables horizontal scalability of redundant brokers. Multiple service provider instances can be supported by a single broker using different URL prefixes and credentials. [Learn more about the Service Broker API.] (https://github.com/openservicebrokerapi/servicebroker/). Note the [topic on orphan resolution](https://github.com/openservicebrokerapi/servicebroker/blob/master/_spec.md#orphans). It is not dealt with in this spec. 
    """
)

