"""

This script runs all CMFPlone tests with our PAS user folder instead of the
standard GRUF in order to flush out changes that need to be made. Usage:

% python seeWhatBreaks.py testFoo testBar

The arguments are module names in CMFPlone/tests. They are imported (as opposed
to execfile'd) so you don't need the '.py' extension. If no args are given, all
tests will be run.

"""

# framework is copied over from CMFPlone/tests
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# use our PloneTestCase, not CMFPlone's
import PloneTestCase
from Products.CMFPlone.tests import PloneTestCase as BaseModule
BaseModule.PloneTestCase = PloneTestCase.PloneTestCase

# but run CMFPlone's tests, not ours
from Products.CMFCore import utils
CMFPLONE_TESTS = os.sep.join(('CMFPlone','tests'))
CMFPLONE_TESTS = utils.expandpath(CMFPLONE_TESTS)

# prime our test runner
import unittest
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()

# get our tests
tests = sys.argv[1:]
if not tests:
    tests = os.listdir(CMFPLONE_TESTS)
    tests = [n[:-3] for n in tests if n.startswith('test') \
                                  and n.endswith('.py')]
for test in tests:
    g = globals()
    m = __import__('Products.CMFPlone.tests.'+test,g,g,test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())

# ... and run them!
if __name__ == '__main__':
    TestRunner().run(suite)
