#!/usr/bin/env python3

import os

import setuptools


def parse_requirements(path):
    full_path = os.path.join(os.path.dirname(__file__), path)
    with open(full_path) as f:
        return [s.strip() for s in f.readlines()
                if (s.strip() and not s.startswith("#"))]


setuptools.setup(
    name='stravaviz',
    version='0.0.1',
    install_requires=parse_requirements("requirements.txt"),
    tests_require=parse_requirements("requirements-dev.txt"),
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'stravaviz = stravaviz.cli:main',
        ],
    },
)
