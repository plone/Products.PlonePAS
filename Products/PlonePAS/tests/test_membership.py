##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id$
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing import ZopeTestCase
from PlonePASTestCase import PlonePASTestCase

from zope.component import getUtility
from Products.CMFCore.interfaces import IMembershipTool

class TestMemberFolder(PlonePASTestCase):

    def afterSetUp(self):
        self.mt = getUtility(IMembershipTool)

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
