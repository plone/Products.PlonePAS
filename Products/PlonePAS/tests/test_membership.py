"""
$Id: test_membership.py,v 1.4 2005/05/24 18:48:17 dreamcatcher Exp $
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
del PloneTestCase

from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tests.PloneTestCase import PloneTestCase

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
