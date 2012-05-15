#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement
import codecs
import os

try:
    from setuptools import setup, find_packages, Command
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages, Command

from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import sys

import djangofeeds

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != "":
    os.chdir(root_dir)
src_dir = "djangofeeds"


def osx_install_data(install_data):
    def finalize_options(self):
        self.set_undefined_options("install", ("install_lib", "install_dir"))
        install_data.finalize_options(self)


class RunTests(Command):
    description = "Run the django test suite from the tests dir."

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        this_dir = os.getcwd()
        testproj_dir = os.path.join(this_dir, "tests")
        os.chdir(testproj_dir)
        sys.path.insert(0, testproj_dir)
        from django.core.management import execute_manager
        os.environ["DJANGO_SETTINGS_MODULE"] = os.environ.get(
                        "DJANGO_SETTINGS_MODULE", "settings")
        settings_file = os.environ["DJANGO_SETTINGS_MODULE"]
        settings_mod = __import__(settings_file, {}, {}, [""])
        execute_manager(settings_mod, argv=[
            __file__, "test"])
        os.chdir(this_dir)


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == "":
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


for scheme in INSTALL_SCHEMES.values():
    scheme["data"] = scheme["purelib"]


for dirpath, dirnames, filenames in os.walk(src_dir):
    # Ignore dirnames that start with "."
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    for filename in filenames:
        if filename.endswith(".py"):
            packages.append(".".join(fullsplit(dirpath)))
        else:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in
                filenames]])


def requirements(fh):
    for line in fh:
        entry = line.strip()
        if not entry.startswith("#"):
            yield entry

install_requires = []
for req in ("requirements/default.txt", ):
    with file(req) as reqfh:
        install_requires.extend(list(requirements(reqfh)))

setup(
    name="django-feeds",
    version=djangofeeds.__version__,
    description=djangofeeds.__doc__,
    author=djangofeeds.__author__,
    author_email=djangofeeds.__contact__,
    packages=packages,
    url=djangofeeds.__homepage__,
    cmdclass={"test": RunTests},
    zip_safe=False,
    data_files=data_files,
    install_requires=install_requires,
    classifiers=[
        "Framework :: Django",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    long_description=codecs.open("README", "r", "utf-8").read(),
)
