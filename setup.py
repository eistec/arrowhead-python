#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import io
import os
import sys

import ast
version = '0.0.unknown'
with open('soa/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = ast.parse(line).body[0].value.s
            break

here = os.path.abspath(os.path.dirname(__file__))

# Remember to add requirements.txt to MANIFEST.in
with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

try:
    with open('requirements-tests.txt') as f:
        tests_require = f.read().splitlines()
except:
    # the tests and requirements-tests.txt is not included with the pip package
    tests_require = []

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
        self.test_args = ['--pylint','--cov','soa','soa','tests']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='soa',
    version=version,
    url='https://github.com/eistec/arrowhead-python/',
    download_url='https://github.com/eistec/arrowhead-python/archive/v0.2.0.tar.gz',
    license='Apache Software License',
    author='Joakim Nohlgård',
    tests_require=tests_require,
    install_requires=install_requires,
    cmdclass={'test': PyTest},
    author_email='joakim.nohlgard@eistec.se',
    description='Arrowhead core services',
    long_description=long_description,
    packages=['soa','soa.directory'],
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
    keywords=[
        'arrowhead',
        'soa',
        'service',
        'iot',
        'coap',
    ],
    extras_require={
        'testing': ['pytest'],
    }
)
