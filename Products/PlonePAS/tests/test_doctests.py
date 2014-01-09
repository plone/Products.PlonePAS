import unittest
import doctest

from Products.PlonePAS.tests import base

from plone.testing import layered
from plone.app.testing.bbb import PTC_FUNCTIONAL_TESTING


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(layered(
        doctest.DocFileSuite('cookie_auth.txt', package='Products.PlonePAS.tests',
                             optionflags=doctest.ELLIPSIS),
        layer=PTC_FUNCTIONAL_TESTING))
    suite.addTest(doctest.DocTestSuite('Products.PlonePAS.utils')),
    return suite
