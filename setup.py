#!/usr/bin/env python3
from codecs import open
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def read(*parts):
    with open(path.join(here, *parts), 'r') as fp:
        return fp.read()


setup(
    name='quart-doh',
    version='0.0.1',
    description='A client and proxy implementation of '
                'https://tools.ietf.org/html/draft-ietf-doh-dns-over-https-13',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/treussart/quart-doh',
    author='Matthieu Treussart',
    author_email='matthieu@treussart.com',
    license="BSD License",
    classifiers=[
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Utilities',
    ],
    keywords='doh dns https',
    packages=['quart_doh'],
    install_requires=[
        'quart >= 0.10.0',
        'dnspython >= 1.16.0',
        'requests >= 2.22.0',
    ],
    tests_require=[
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'doh-client = quart_doh.client:main',
            'doh-server = quart_doh.server:main',
        ],
    },
)
