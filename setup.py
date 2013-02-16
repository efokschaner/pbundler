#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

extra = {
    'install_requires': ['distribute']
}

if sys.version_info >= (3,):
    extra['use_2to3'] = False

setup(
    name="pbundler",
    version="0.8.0DEV",
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'pbundle = pbundler.cli:pbcli',
            'pbundle-py = pbundler.cli:pbpy',
        ],
    },

    # metadata for upload to PyPI
    author="Christian Hofstaedtler",
    author_email="ch--pypi@zeha.at",
    description="Bundler for Python",
    license="MIT",
    keywords="bundler bundle pbundler pbundle dependency dependencies management virtualenv pip packages",
    url="http://github.com/zeha/pbundler/",
    download_url="https://github.com/zeha/pbundler/downloads",
    **extra
)

