import unittest
from PlonePASTestCase import PlonePASTestCase
from Products.PlonePAS.browser.search import PASSearchView

class TestSearchView(PlonePASTestCase):
    def testBasicSearch(self):
        view=PASSearchView(None, None)
        self.assertEqual(results, [{'userid': 'foo'}, {'userid': 'bar'}])

    def testSortingSearch(self):
        view=PASSearchView(None, None)
        self.assertEqual(view.sort(results, 'userid'), [{'userid': 'bar'}, {'userid': 'foo'}])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSearchView))
    return suite
