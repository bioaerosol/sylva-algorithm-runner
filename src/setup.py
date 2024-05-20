#!/usr/bin/env python3

from setuptools import setup, find_packages

import sylva_algorithm_runner as sylva_algorithm_runner

setup(
    name='sylva_algorithm_runner',
    packages=find_packages(where="."),
    package_dir={"sylva_algorithm_runner": "./sylva_algorithm_runner"},
    install_requires=[
        "pyyaml==6.0.1",
        "requests==2.31.0",
        "pymongo==4.7.2",
        "bottle==0.12.25",
        "python-dateutil==2.8.0"
    ],
    tests_require=[],
    version=sylva_algorithm_runner.__version__,
    description='',
    download_url='',
    long_description="""""",
    platforms='OS Independent',
    classifiers=[],
)