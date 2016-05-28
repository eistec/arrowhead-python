#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import io
import os
import sys

import arrowhead

here = os.path.abspath(os.path.dirname(__file__))

# Remember to add requirements.txt to MANIFEST.in
with open('requirements.txt') as f:
    required = f.read().splitlines()

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.rst')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--pylint','--cov','arrowhead']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='arrowhead',
    version=arrowhead.__version__,
    url='http://github.com/eistec/arrowhead-python/',
    license='Apache Software License',
    author='Joakim Nohlgård',
    tests_require=['pytest','pylint','coverage','pytest-cov','pytest-pylint'],
    install_requires=required,
    cmdclass={'test': PyTest},
    author_email='joakim.nohlgard@eistec.se',
    description='Arrowhead core services',
    long_description=long_description,
    packages=['arrowhead','arrowhead.servicedirectory'],
    include_package_data=True,
    platforms='any',
    classifiers = [
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: Name Service (DNS)',
        ],
    extras_require={
        'testing': ['pytest'],
    }
)
