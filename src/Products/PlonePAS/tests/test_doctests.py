# -*- coding: utf-8 -*-
from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING
from plone.testing import layered

import doctest
import re
import six
import unittest


class Py23DocChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        if six.PY2:
            got = re.sub("IOError", "OSError", got)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(
        layered(
            doctest.DocFileSuite(
                'cookie_auth.rst',
                package='Products.PlonePAS.tests',
                optionflags=doctest.ELLIPSIS,
                checker=Py23DocChecker(),
            ),
            layer=PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING
        )
    )
    suite.addTest(
        doctest.DocTestSuite(
            'Products.PlonePAS.utils',
            optionflags=doctest.ELLIPSIS,
            checker=Py23DocChecker(),
        )
    )
    return suite
