from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_INTEGRATION_TESTING

import unittest


class TestPASSearchView(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def test_sort(self):
        self.portal = self.layer["portal"]
        pas_search = self.portal.restrictedTraverse("@@pas_search")
        values = [
            {"title": "Sociologie"},
            {"title": "Économie"},
            {"title": "anthropologie"},
        ]
        sorted_values = pas_search.sort(values, "title")
        # do not modify original
        self.assertEqual(
            values,
            [
                {"title": "Sociologie"},
                {"title": "Économie"},
                {"title": "anthropologie"},
            ],
        )
        # sorted here
        self.assertEqual(
            sorted_values,
            [
                {"title": "anthropologie"},
                {"title": "Économie"},
                {"title": "Sociologie"},
            ],
        )
