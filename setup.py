# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "fair_eva"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion==2.6.0",
    "swagger-ui-bundle==0.0.6",
]

setup(
    name=NAME,
    version=VERSION,
    description="FAIR Eva API",
    author_email="",
    url="",
    keywords=["OpenAPI", "FAIR API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['fair-api.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['openapi_server=fair:main']},
    long_description="""\
    API for evaluate FAIRness of digital objects in repositories.
    """
)
