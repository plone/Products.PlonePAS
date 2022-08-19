from plone.testing import layered
from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING

import doctest
import re
import unittest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(
        layered(
            doctest.DocFileSuite(
                "cookie_auth.rst",
                package="Products.PlonePAS.tests",
                optionflags=doctest.ELLIPSIS,
            ),
            layer=PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING,
        )
    )
    suite.addTest(
        doctest.DocTestSuite(
            "Products.PlonePAS.utils",
            optionflags=doctest.ELLIPSIS,
        )
    )
    return suite
