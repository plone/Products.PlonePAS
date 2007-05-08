import unittest
import doctest

from Testing.ZopeTestCase import ZopeDocFileSuite
from PlonePASTestCase import PlonePASTestCase

def test_suite():
    suite = ZopeDocFileSuite(
        'browser/search.txt',
        package='Products.PlonePAS',
        optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
        test_class=PlonePASTestCase)
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
