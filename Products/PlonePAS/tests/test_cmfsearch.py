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
$Id: test_membership.py 18307 2006-01-22 17:28:37Z alecm $
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from PlonePASTestCase import PlonePASTestCase

from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins \
                import IUserEnumerationPlugin

class TestCMFSearch(PlonePASTestCase):
    def afterSetUp(self):
        self.mt = getToolByName(self.portal, 'portal_membership')
        self.md = getToolByName(self.portal, 'portal_memberdata')

        self.member_id = 'member1'
        # Create a new Member
        self.mt.addMember(self.member_id, 'pw', ['Member'], [],
                     {'email': 'member1@host.com',
                      'title': 'Member #1'})

        self.pas=getToolByName(self.portal, "acl_users")
        for plugin in self.pas.plugins.getAllPlugins('IUserEnumerationPlugin')['active']:
            self.pas.plugins.deactivatePlugin(IUserEnumerationPlugin, plugin)

        self.pas.manage_addProduct["PlonePAS"].addCMFSearch(
                id="cmfsearch", title="CMF Search plugin")
        self.plugin=self.pas.cmfsearch
        self.pas.plugins.activatePlugin(IUserEnumerationPlugin, 'cmfsearch')


    def testPluginActivate(self):
        plugins = self.pas.plugins.getAllPlugins('IUserEnumerationPlugin')['active']
        self.assertEqual('cmfsearch' in plugins, True)


    def testSimpleSearch(self):
        self.assertEqual(
            self.plugin.enumerateUsers(email="something@somewhere.tld",
                    exact_match=False),
            [] )


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCMFSearch))
    return suite

if __name__ == '__main__':
    framework()
