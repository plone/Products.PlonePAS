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
"""

import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from PlonePASTestCase import PlonePASTestCase

from cStringIO import StringIO
from zExceptions import BadRequest
from Acquisition import aq_base, aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tools.memberdata import MemberData
from Products.PlonePAS.plugins.ufactory import PloneUser

class MembershipToolTest(PlonePASTestCase):

    def afterSetUp(self):
        self.mt = mt = getToolByName(self.portal, 'portal_membership')
        self.md = md = getToolByName(self.portal, 'portal_memberdata')

        self.member_id = 'member1'
        # Create a new Member
        mt.addMember(self.member_id, 'pw', ['Member'], [],
                     {'email': 'member1@host.com',
                      'title': 'Member #1'})

    def test_get_member(self):
        member = self.portal.acl_users.getUserById(self.member_id)
        self.failIf(member is None)

        # Should be wrapped into the PAS.
        got = aq_base(aq_parent(member))
        expected = aq_base(self.portal.acl_users)
        self.assertEquals(got, expected)

        self.failUnless(isinstance(member, PloneUser))

    def test_get_member_by_id(self):
        # Use tool way of getting member by id. This returns a
        # MemberData object wrapped by the member
        member = self.mt.getMemberById(self.member_id)
        self.failIf(member is None)
        self.failUnless(isinstance(member, MemberData))
        self.failUnless(isinstance(aq_parent(member), PloneUser))

    def test_id_clean(self):
        from Products.PlonePAS.utils import cleanId, decleanId
        a = [
             "asdfasdf",
             "asdf-asdf",
             "asdf--asdf",
             "asdf---asdf",
             "asdf----asdf",
             "asdf-----asdf",
             "asdf%asdf",
             "asdf%%asdf",
             "asdf%%%asdf",
             "asdf%%%%asdf",
             "asdf%%%%%asdf",
             "asdf-%asdf",
             "asdf%-asdf",
             "asdf-%-asdf",
             "asdf%-%asdf",
             "asdf--%asdf",
             "asdf%--asdf",
             "asdf--%-asdf",
             "asdf-%--asdf",
             "asdf--%--asdf",
             "asdf%-%asdf",
             "asdf%--%asdf",
             "asdf%---%asdf",
             "-asdf",
             "--asdf",
             "---asdf",
             "----asdf",
             "-----asdf",
             "asdf-",
             "asdf--",
             "asdf---",
             "asdf----",
             "asdf-----",
             "%asdf",
             "%%asdf",
             "%%%asdf",
             "%%%%asdf",
             "%%%%%asdf",
             "asdf%",
             "asdf%%",
             "asdf%%%",
             "asdf%%%%",
             "asdf%%%%%",
             "asdf\x00asdf",
        ]
        b = [cleanId(id) for id in a]
        c = [decleanId(id) for id in b]
        ac = zip(a,c)
        for aa, cc in ac:
            self.failUnless(aa==cc)

class MemberAreaTest(PlonePASTestCase):

    def afterSetUp(self):
        self.mt = mt = getToolByName(self.portal, 'portal_membership')
        self.md = md = getToolByName(self.portal, 'portal_memberdata')
        # Enable member-area creation
        self.mt.memberareaCreationFlag = 1
        # Those are all valid chars in Zope.
        self.mid = "Member #1 - Houston, TX. ($100)"
        self.loginAsPortalOwner()

    def test_funky_member_ids_1(self):
        mid = self.mid
        minfo = (mid, 'pw', ['Member'], [])

        # Create a new User
        self.portal.acl_users._doAddUser(*minfo)
	self.mt.createMemberArea,(mid)

    def test_funky_member_ids_2(self):
        # Forward-slash is not allowed
        mid = self.mid + '/'
        minfo = (mid, 'pw', ['Member'], [])

        # Create a new User
        self.portal.acl_users._doAddUser(*minfo)
        self.mt.createMemberArea(mid)

    def test_memberareaCreationFlag_respected(self):
        self.portal.acl_users._doAddUser('foo', 'pw', ['Member'], [])
        self.portal.acl_users._doAddUser('bar', 'pw', ['Member'], [])

        self.failIf('foo' in self.portal.Members.objectIds())
        self.failIf('bar' in self.portal.Members.objectIds())

        self.mt.createMemberarea('foo')
        self.failUnless('foo' in self.portal.Members.objectIds())

        self.mt.memberareaCreationFlag = 0
        self.mt.createMemberArea('bar')
        self.failIf('bar' in self.portal.Members.objectIds())

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MembershipToolTest))
    suite.addTest(unittest.makeSuite(MemberAreaTest))
    return suite

