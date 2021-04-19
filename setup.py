#!/usr/bin/env python
from setuptools import setup

setup(
    name='tap-coosto',
    version='0.1.0',
    description='Singer.io tap for extracting data',
    author='Stitch',
    url='http://singer.io',
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['tap_coosto'],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        'singer-python',
        'httpx',
        'httpx[http2]',
        'pause',
    ],
    entry_points="""
    [console_scripts]
    tap-coosto=tap_coosto:main
    """,
    packages=['tap_coosto'],
    package_data={
        'schemas': ['tap_coosto/schemas/*.json']
    },
    include_package_data=True,
)
