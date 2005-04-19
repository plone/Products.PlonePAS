import os, sys
import unittest
from sets import Set
import traceback

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing                 import ZopeTestCase
from Products.CMFCore.utils  import getToolByName
from PloneTestCase import PloneTestCase


# This is the test case. You will have to add test_<methods> to your
# class inorder to assert things about your Product.
class TestMemberFolder(PloneTestCase):

    def test_folder(self):
        assert self.portal.portal_membership.getHomeFolder()

    def test_membershipId(self):
        u = self.portal.portal_membership.getAuthenticatedMember().getId()
        assert u == ZopeTestCase.user_name

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMemberFolder))
    return suite

if __name__ == '__main__':
    framework()
