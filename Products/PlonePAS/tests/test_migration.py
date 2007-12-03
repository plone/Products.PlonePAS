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

from Acquisition import aq_base, aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName

class SanityCheck:

    _users = (
        ('user1', 'u1', ['Member'], [],
         {'email': 'user1@host.com',
          'fullname': 'User #1',
          }
         ),
        ('user2', 'u2', ['Member', 'Reviewer'], [],
         {'email': 'user2@host.com',
          'fullname': 'User #2',
          }
         ),
        ('user3', 'u3', [], [],
         {'email': 'user3@host.com',
          'fullname': 'User #3',
          }
         ),
        ('user4', 'u4', [], [],
         {'email': 'user4@host.com',
          'fullname': 'User #4',
          }
         ),
        )

    _groups = (
        ('group0', ['Member'], [],
         {'title': 'Group #0',
          'description': 'Group #0 Description',
          'email': 'group0@host.com',
          }
         ),
        ('group1', ['Member'], [],
         {'title': 'Group #1',
          'description': 'Group #1 Description',
          'email': 'group1@host.com',
          }
         ),
        ('group2', ['Reviewer'], ['group0'],
         {'title': 'Group #2',
          'description': 'Group #2 Description',
          'email': 'group2@host.com',
          }
         ),
        )

    _group_members = {
        'group0': ('user4',),
        'group1': ('user3',),
        'group2': ('user1', 'user2'),
        }

    def __init__(self, testcase, portal):
        self.portal = portal
        self.tc = testcase

    def uf(self):
        return getToolByName(self.portal, 'acl_users')

    def checkUserFolder(self):
        uf = self.uf()
        self.tc.failUnless(uf.meta_type == 'Pluggable Auth Service',
                           uf.meta_type)
        parent = aq_parent(aq_inner(uf))
        self.tc.failUnless(aq_base(parent) == aq_base(self.portal),
                           (parent, self.portal, uf))

    def checkUsers(self):
        mt = getToolByName(self.portal, 'portal_membership')
        md = getToolByName(self.portal, 'portal_memberdata')
        propids = md.propertyIds()
        uf = self.uf()
        for uid, upw, uroles, udomains, uprops in self._users:
            user = uf.getUserById(uid)
            self.tc.failIf(user is None, uid)

            # Ignore password check?
            # pw = user.getPassword()
            # self.tc.failUnless(pw == upw, (uid, pw, upw)

            roles = [r for r in user.getRoles() if r not in ('Authenticated',)]
            for role in uroles:
                self.tc.failUnless(role in roles, (uid, role, roles))

            # Ignore domains check?
            # domains = user.getDomains()
            # self.tc.failUnless(domains == udomains, (uid, domains, udomains))

            member = mt.getMemberById(uid)

            for k, v in uprops.items():
                propval = member.getProperty(k, None)
                self.tc.failUnless(propval == v, (uid, k, propval, v))

    def checkGroups(self):
        gt = getToolByName(self.portal, 'portal_groups')
        gd = getToolByName(self.portal, 'portal_groupdata')
        propids = gd.propertyIds()
        for gid, groles, gsubs, gprops in self._groups:
            group = gt.getGroupById(gid)
            self.tc.failIf(group is None, gid)

            roles = [r for r in group.getRoles() if r != 'Authenticated']
            for role in groles:
                self.tc.failUnless(role in roles, (gid, role, roles))

            # XXX fails currently because getGroupMembers tries to do
            # getUserById with the group id and PAS looks only at
            # IUserEnumeration.
            # members = group.getGroupMemberIds()
            # expected = self._group_members[gid]
            # for member in expected:
            #     self.tc.failUnless(member in members, (gid, member, members))

            # XXX This seems to be expected to break too.
            for k, v in gprops.items():
                propval = group.getProperty(k, None)
                self.tc.failUnless(propval == v, (gid, k, propval, v))

    def populateUsers(self):
        mt = getToolByName(self.portal, 'portal_membership')
        for u in self._users:
            member = mt.getMemberById(u[0])
            if member is None:
                mt.addMember(*u)
            else:
                member.setMemberProperties(u[-1])


    def populateGroups(self):
        gt = getToolByName(self.portal, 'portal_groups')
        for g in self._groups:
            try:
                gt.addGroup(*g[:-1], **g[-1])
            except TypeError:
                # GRUF 2.x doesn't accept properties in addgroup
                gt.addGroup(g[0],"",*g[1:-1])   # old addGroup uses password
                group = gt.getGroupById(g[0])
                group.setGroupProperties(g[-1])

            gid = g[0]
            group = gt.getGroupById(gid)
            for mid in self._group_members[gid]:
                group.addMember(mid)

    def run(self, *actions):
        for name in actions:
            getattr(self, name)()

class BaseTest(PlonePASTestCase):

    vanilla_plone = True

    def afterSetUp(self):
        self.checker = SanityCheck(self, self.portal)

class MigrationTest(BaseTest):

    def afterSetUp(self):
        BaseTest.afterSetUp(self)
        self.qi = getToolByName(self.portal, 'portal_quickinstaller')

    def test_migrate_no_user_folder_empty(self):
        self.loginAsPortalOwner()
        if 'acl_users' in self.portal.objectIds():
            self.portal.manage_delObjects(ids=['acl_users'])

        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        self.checker.run('checkUserFolder')

    def test_migrate_memberdata_with_selection_property(self):
        self.loginAsPortalOwner()
        pm = getToolByName(self.portal, 'portal_memberdata')
        pm._setProperty('select_choice', ('A', 'B', 'C'), 'lines')
        pm._setProperty('choice', 'select_choice', 'selection')
        pm._updateProperty('choice', 'A')
        property = pm.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = pm.getProperty('choice')
        self.assertEquals(property, 'A')
        
        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        
        pm = getToolByName(self.portal, 'portal_memberdata')
        property = pm.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = pm.getProperty('choice')
        self.assertEquals(property, 'A')

    def test_migrate_memberdata_with_multiple_selection_property(self):
        self.loginAsPortalOwner()
        pm = getToolByName(self.portal, 'portal_memberdata')
        pm._setProperty('select_choice', ('A', 'B', 'C'), 'lines')
        pm._setProperty('choice', 'select_choice', 'multiple selection')
        pm._updateProperty('choice', ('A', 'C'))
        property = pm.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = pm.getProperty('choice')
        self.assertEquals(property, ('A', 'C'))
        
        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        
        pm = getToolByName(self.portal, 'portal_memberdata')
        property = pm.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = pm.getProperty('choice')
        self.assertEquals(property, ('A', 'C'))

    def test_migrate_groupdata_with_selection_property(self):
        self.loginAsPortalOwner()
        gd = getToolByName(self.portal, 'portal_groupdata')
        gd._setProperty('select_choice', ('A', 'B', 'C'), 'lines')
        gd._setProperty('choice', 'select_choice', 'selection')
        gd._updateProperty('choice', 'A')
        property = gd.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = gd.getProperty('choice')
        self.assertEquals(property, 'A')
        
        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        
        gd = getToolByName(self.portal, 'portal_groupdata')
        property = gd.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = gd.getProperty('choice')
        self.assertEquals(property, 'A')

    def test_migrate_groupdata_with_multiple_selection_property(self):
        self.loginAsPortalOwner()
        gd = getToolByName(self.portal, 'portal_groupdata')
        gd._setProperty('select_choice', ('A', 'B', 'C'), 'lines')
        gd._setProperty('choice', 'select_choice', 'multiple selection')
        gd._updateProperty('choice', ('A', 'C'))
        property = gd.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = gd.getProperty('choice')
        self.assertEquals(property, ('A', 'C'))
        
        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        
        gd = getToolByName(self.portal, 'portal_groupdata')
        property = gd.getProperty('select_choice')
        self.assertEquals(property, ('A', 'B', 'C'))
        property = gd.getProperty('choice')
        self.assertEquals(property, ('A', 'C'))

    def test_migrate_no_user_folder_populated_users(self):
        # XXX This will never work: removing acl_users means loosing all login
        # information, so there is nothing useful to (re)create users
        self.loginAsPortalOwner()
        if 'acl_users' in self.portal.objectIds():
            self.portal.manage_delObjects(ids=['acl_users'])

        self.checker.run('populateUsers')
        # Don't remove the tools
        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        self.checker.run('checkUserFolder', 'checkUsers')

    def test_migrate_normal_uf_no_group_tools(self):
        self.loginAsPortalOwner()
        if 'acl_users' in self.portal.objectIds():
            self.portal.manage_delObjects(ids=['acl_users'])
        to_remove = ('portal_groups', 'portal_groupdata')
        for tname in to_remove:
            if tname in self.portal.objectIds():
                self.portal.manage_delObjects(ids=[tname])

        self.checker.run('populateUsers')
        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        self.checker.run('checkUserFolder', 'checkUsers')

    def test_migrate_populated(self):
        self.loginAsPortalOwner()
        self.checker.run('populateUsers', 'populateGroups',
                         'checkUsers', 'checkGroups')

        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        self.checker.run('checkUserFolder', 'checkUsers', 'checkGroups')

    def test_migrate_populated_gruf_no_group_tools(self):
        self.loginAsPortalOwner()
        self.checker.run('populateUsers', 'populateGroups')
        to_remove = ('portal_groups', 'portal_groupdata')
        for tname in to_remove:
            if tname in self.portal.objectIds():
                self.portal.manage_delObjects(ids=[tname])

        self.qi.uninstallProducts(['PlonePAS'], reinstall=True)
        self.qi.installProduct('PlonePAS', reinstall=True)
        self.checker.run('checkUserFolder', 'checkUsers')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrationTest))
    return suite

