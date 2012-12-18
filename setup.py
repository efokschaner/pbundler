#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

extra = {
    'install_requires': ['distribute', 'pip>=1.1']
}

if sys.version_info >= (3,):
    extra['use_2to3'] = False

try:
    import venv
except:
    # on 3.3+, we'll use venv instead, which is bundled with the interpreter.
    extra['install_requires'].append('virtualenv>=1.7')

setup(
    name="pbundler",
    version="0.0.6",
    packages=find_packages(),
    zip_safe=False,
    package_data={
        '': ['*.md'],
    },
    entry_points={
        'console_scripts': [
            'pbundle = PBundler.entrypoints:pbcli',
            'pbundle-py = PBundler.entrypoints:pbpy',
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

