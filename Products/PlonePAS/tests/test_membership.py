"""
$Id: test_membership.py,v 1.3 2005/05/24 17:44:37 dreamcatcher Exp $
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFCore.utils import getToolByName
from PloneTestCase import PloneTestCase

class TestMemberFolder(PloneTestCase):

    def afterSetUp(self):
        self.mt = getToolByName(self.portal, 'portal_membership')

    def test_folder(self):
        assert self.mt.getHomeFolder() is not None

    def test_membershipId(self):
        u = self.mt.getAuthenticatedMember().getId()
        assert u == ZopeTestCase.user_name

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMemberFolder))
    return suite

if __name__ == '__main__':
    framework()
