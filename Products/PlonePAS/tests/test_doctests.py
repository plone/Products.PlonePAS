import unittest
from Testing import ZopeTestCase

from Products.PlonePAS.tests import base


def test_suite():
    suite = unittest.TestSuite()
    DocFileSuite = ZopeTestCase.FunctionalDocFileSuite
    DocTestSuite = ZopeTestCase.FunctionalDocTestSuite
    tests = (
        ('cookie_auth.txt', base.FunctionalTestCase),
        )

    for fname, klass in tests:
        t = DocFileSuite(fname,
                         test_class=klass,
                         package='Products.PlonePAS.tests')
        suite.addTest(t)
    suite.addTest(DocTestSuite('Products.PlonePAS.utils')),
    return suite
