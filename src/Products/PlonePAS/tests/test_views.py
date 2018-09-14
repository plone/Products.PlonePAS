# -*- encoding: utf-8 -*-
from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_INTEGRATION_TESTING

import unittest


class TestPASSearchView(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def test_sort(self):
        self.portal = self.layer['portal']
        pas_search = self.portal.restrictedTraverse('@@pas_search')
        values = [{'title': u'Sociologie'}, {'title': u'Économie'},
                  {'title': u'anthropologie'}]
        sorted_values = pas_search.sort(values, 'title')
        # do not modify original
        self.assertEqual(values,
                         [{'title': u'Sociologie'}, {'title': u'Économie'},
                          {'title': u'anthropologie'}])
        # sorted here
        self.assertEqual(sorted_values,
                         [{'title': u'anthropologie'}, {'title': u'Économie'},
                          {'title': u'Sociologie'}])
