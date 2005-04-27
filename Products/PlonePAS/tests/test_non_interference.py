import os, sys
import unittest
from sets import Set
import traceback

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Products.CMFCore.utils  import getToolByName

# Tests to ensure that our monkeypatches don't interfere w/ normal
# operations when PlonePAS is not installed

# import original PloneTestCase instead of our own version
from Products.CMFPlone.tests import PloneTestCase
from Products.PlonePAS.plone import searchForMembers

class TestMemberFolder(PloneTestCase.PloneTestCase):

    def test_search(self):
        # plone calls portal_membership.searchForMembers (thru
        # prefs_user_group_search) w/ a "name" parameter set to the
        # empty string. this can't give out an error
        self.assertEquals(self.portal.portal_membership.searchForMembers.im_func,
                          searchForMembers)
                          
        self.portal.portal_membership.searchForMembers(REQUEST=None,
                                                       name="")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMemberFolder))
    return suite

if __name__ == '__main__':
    framework()
