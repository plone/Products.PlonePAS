"""

run all CMFPlone tests with our PAS user folder instead of the standard GRUF

"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# put our PloneTestCase in CMFPlone/runallatest.py's way
import PloneTestCase
from Products.CMFPlone.tests import PloneTestCase as BaseModule
BaseModule.PloneTestCase = PloneTestCase.PloneTestCase

# run CMFPlone's tests, not ours
from Products.CMFCore import utils
CMFPLONE_TESTS = os.sep.join(('CMFPlone','tests'))
CMFPLONE_TESTS = utils.expandpath(CMFPLONE_TESTS)

# and now actually run the tests
import unittest
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()

tests = os.listdir(CMFPLONE_TESTS)
tests = [n[:-3] for n in tests if n.startswith('test') and n.endswith('.py')]

for test in tests:
    g = globals()
    m = __import__('Products.CMFPlone.tests.'+test,g,g,test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())

if __name__ == '__main__':
    TestRunner().run(suite)
