"""
Unit tests subpackage for hlc
"""
import unittest
import sys

import hlc.test.objects

def run(verbosity=1):
    """
    Run all tests from imported submodules of this package
    """
    self = sys.modules[__name__]
    submodules = list()
    for attr in dir(self):
        x = getattr(self, attr)
        if type(x) == type(self) \
        and x.__name__.startswith(__name__):
            submodules.append(x)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for m in submodules:
        suite.addTests(loader.loadTestsFromModule(m))

    unittest.TextTestRunner(
        buffer=True,
        verbosity=verbosity
    ).run(suite)
