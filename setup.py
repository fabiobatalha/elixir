#!/usr/bin/env python
import sys
import re
from setuptools import setup, Extension

install_requires = [
    'requests',
    'xylose',
    'lxml'
]

tests_require = []

setup(
    name="elixir",
    version="0.1",
    description="Library to bring alive the legacy documents from the SciELO Methodology",
    author="Fabio Batalha",
    author_email="scielo-dev@googlegroups.com",
    license="BSD 2-Clause",
    url="http://github.com/scieloorg/elixir/",
    py_modules=["elixir"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    dependency_links=['http://github.com/scieloorg/xylose/tarball/master#egg=xylose'],
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite="tests",
)
