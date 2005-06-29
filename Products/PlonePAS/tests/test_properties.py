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
$Id: test_properties.py,v 1.8 2005/06/29 17:27:46 jccooper Exp $
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing import ZopeTestCase
from Products.PlonePAS.tests import PloneTestCase

from cStringIO import StringIO
from Acquisition import aq_base, aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName

class PropertiesTest(PloneTestCase.PloneTestCase):

    def test_user_properties(self):
        mt = getToolByName(self.portal, 'portal_membership')
        md = getToolByName(self.portal, 'portal_memberdata')

        # Create a new Member
        mt.addMember('user1', 'u1', ['Member'], [],
                     {'email': 'user1@host.com',
                      'fullname': 'User #1'})
        member = mt.getMemberById('user1')
        self.failIf(member is None)

        # Assert user doesn't have the property yet
        self.failIf(member.hasProperty('age'))

        # Add new property
        md.manage_addProperty('age', 20, 'int')

        # Assert user has the property now
        self.failUnless(member.hasProperty('age'))

        # Get the property, should have the default value
        got = member.getProperty('age', None)
        expected = 20
        self.assertEquals(got, expected)

        # get a handle on the member
        member = mt.getMemberById('user1')

        # Set some member properties. Needs to be logged in as the user.
        self.login('user1')
        member.setMemberProperties({'age':30, 'fullname':'User #1 Is Cool',
                                    'email':'user1@anotherhost.qa'})

        # Check the properties have been set
        got = member.getProperty('age', None)
        expected = 30
        self.assertEquals(got, expected)

        got = member.getProperty('fullname', None)
        expected = 'User #1 Is Cool'
        self.assertEquals(got, expected)

        got = member.getProperty('email', None)
        expected = 'user1@anotherhost.qa'
        self.assertEquals(got, expected)

        # Delete the property
        md.manage_delProperties(ids=('age',))

        # re-get the member to reflect the new memberdata schema
        member = mt.getMemberById('user1')

        # Assert property is gone
        self.failIf(member.hasProperty('age'))

        # Get the property, should return default (None)
        got = member.getProperty('age', None)
        expected = None
        self.assertEquals(got, expected)

        # Other properties should still be there.
        got = member.getProperty('fullname', None)
        expected = 'User #1 Is Cool'
        self.assertEquals(got, expected)

        got = member.getProperty('email', None)
        expected = 'user1@anotherhost.qa'
        self.assertEquals(got, expected)

    def test_group_properties(self):
        gt = getToolByName(self.portal, 'portal_groups')
        gd = getToolByName(self.portal, 'portal_groupdata')

        self.loginPortalOwner()

        # Create a new Group
        gt.addGroup('group1', ['Reviewer'], [],
                     {'email': 'group1@host.com',
                      'title': 'Group #1'})
        group = gt.getGroupById('group1')
        self.failIf(group is None)

        # Assert group doesn't have the property yet
        self.failIf(group.hasProperty('karma'))

        # Add new property
        gd.manage_addProperty('karma', 20, 'int')

        # get group again to re-create with new groupdata schema
        group = gt.getGroupById('group1')

        # Assert group has the property now
        self.failUnless(group.hasProperty('karma'))

        # Get the property, should have the default value
        got = group.getProperty('karma', None)
        expected = 20

        self.assertEquals(got, expected)

        # Set some group properties
        group.setGroupProperties({'karma':30, 'title':'Group #1 Is Cool',
                                  'email':'group1@anotherhost.qa'})

        # Check the properties have been set
        got = group.getProperty('karma', None)
        expected = 30
        self.assertEquals(got, expected)

        got = group.getProperty('title', None)
        expected = 'Group #1 Is Cool'
        self.assertEquals(got, expected)

        got = group.getProperty('email', None)
        expected = 'group1@anotherhost.qa'
        self.assertEquals(got, expected)

        # Delete the property
        gd.manage_delProperties(ids=('karma',))

        # get group again to re-create with new groupdata schema
        group = gt.getGroupById('group1')

        # Assert property is gone
        self.failIf(group.hasProperty('karma'))

        # Get the property, should return default (None)
        got = group.getProperty('karma', None)
        expected = None
        self.assertEquals(got, expected)

        # Other properties should still be there.
        got = group.getProperty('title', None)
        expected = 'Group #1 Is Cool'
        self.assertEquals(got, expected)

        got = group.getProperty('email', None)
        expected = 'group1@anotherhost.qa'
        self.assertEquals(got, expected)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PropertiesTest))
    return suite

if __name__ == '__main__':
    framework()
