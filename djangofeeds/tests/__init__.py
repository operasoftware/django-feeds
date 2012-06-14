"""Django feeds test suite"""
import unittest
import os


def suite():
    loader = unittest.TestLoader()
    tests = loader.discover(os.path.dirname(__file__),
        pattern='test*.py', top_level_dir=None)

    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(test)

    return suite
