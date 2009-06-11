#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import sys

import djangofeeds

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
src_dir = "djangofeeds"

def osx_install_data(install_data):
    def finalize_options(self):
        self.set_undefined_options("install", ("install_lib", "install_dir"))
        install_data.finalize_options(self)

#if sys.platform == "darwin":
#    cmdclasses = {'install_data': osx_install_data}
#else:
#    cmdclasses = {'install_data': install_data}


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


for dirpath, dirnames, filenames in os.walk(src_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."): del dirnames[i]
    for filename in filenames:
        if filename.endswith(".py"):
            packages.append('.'.join(fullsplit(dirpath)))
        else:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in
                filenames]])

setup(
    name='django-feeds',
    version=djangofeeds.__version__,
    description=djangofeeds.__doc__,
    author=djangofeeds.__author__,
    author_email=djangofeeds.__contact__,
    packages=packages,
    #cmdclass = cmdclasses,
    url=djangofeeds.__homepage__,
    zip_safe=False,
    data_files = data_files,
    install_requires=[
        'feedparser',
        'django',
        'yadayada',
        'django-unittest-depth',
        'celery',
        'django-tagging',

    ],
    classifiers=[
        "Framework :: Django",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    long_description=codecs.open('README.rst', "r", "utf-8").read(),
)
