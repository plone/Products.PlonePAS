"""

run all CMFPlone tests with our PAS user folder instead of the standard GRUF

"""


import os, sys
PRODUCTS_DIR = sys.path[0].split(os.sep)[:-2]
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# put PloneTestCase in CMFPlone/runalltest.py's way
#  have to do this after framework (so we can find other Products) but before
#  switching our sys.path[0]
import PloneTestCase
from Products.CMFPlone.tests import PloneTestCase as BaseModule
BaseModule.PloneTestCase = PloneTestCase.PloneTestCase

# run CMFPlone's tests, not ours
import os, sys
PRODUCTS_DIR.append('CMFPlone')
PRODUCTS_DIR.append('tests')
CMFPLONE_TESTS = os.sep.join(PRODUCTS_DIR)
sys.path[0] = CMFPLONE_TESTS

import unittest
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()

tests = os.listdir(CMFPLONE_TESTS)
tests = [n[:-3] for n in tests if n.startswith('test') and n.endswith('.py')]

for test in tests:
    m = __import__(test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())

if __name__ == '__main__':
    TestRunner().run(suite)