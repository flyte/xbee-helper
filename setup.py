#  -*- coding: utf-8 -*-
"""
Setuptools script for the xbee-helper project.
"""

import os
from textwrap import fill, dedent

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def required(fname):
    return open(
        os.path.join(
            os.path.dirname(__file__), fname
        )
    ).read().split('\n')


setup(
    name="xbee-helper",
    version="0.0.6",
    packages=find_packages(
        exclude=[
            "*.tests",
            "*.tests.*",
            "tests.*",
            "tests",
            "*.ez_setup",
            "*.ez_setup.*",
            "ez_setup.*",
            "ez_setup",
            "*.examples",
            "*.examples.*",
            "examples.*",
            "examples"
        ]
    ),
    scripts=[],
    entry_points={},
    include_package_data=True,
    setup_requires='pytest-runner',
    tests_require='pytest',
    install_requires=required('requirements.txt'),
    test_suite='pytest',
    zip_safe=False,
    # Metadata for upload to PyPI
    author='Ellis Percival',
    author_email="xbee-helper@failcode.co.uk",
    description=fill(dedent("""\
        This project offers a high level API to an XBee device running an
        up-to-date version of the ZigBee firmware. It builds upon the existing
        XBee project by abstracting more functionality into methods.
    """)),
    classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Communications",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Networking"
    ],
    license="MIT",
    keywords="",
    url="https://github.com/flyte/xbee-helper"
)
