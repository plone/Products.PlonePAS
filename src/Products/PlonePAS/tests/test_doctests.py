# -*- coding: utf-8 -*-
from plone.app.testing.bbb import PTC_FUNCTIONAL_TESTING
from plone.testing import layered
import doctest
import unittest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(
        layered(
            doctest.DocFileSuite(
                'cookie_auth.rst',
                package='Products.PlonePAS.tests',
                optionflags=doctest.ELLIPSIS
            ),
            layer=PTC_FUNCTIONAL_TESTING
        )
    )
    suite.addTest(
        doctest.DocTestSuite(
            'Products.PlonePAS.utils',
            optionflags=doctest.ELLIPSIS
        )
    )
    return suite
