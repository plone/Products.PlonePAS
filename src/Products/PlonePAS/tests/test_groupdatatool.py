from AccessControl import Permissions
from AccessControl import Unauthorized
from Acquisition import aq_parent
from plone.app.testing import logout
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_INTEGRATION_TESTING

import unittest


def sortTuple(t):
    l = list(t)
    l.sort()
    return tuple(l)


class TestGroupDataTool(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.acl_users = self.portal.acl_users
        self.groups = self.portal.portal_groups
        self.groupdata = self.portal.portal_groupdata
        self.groups.addGroup("foo")
        # MUST reset _v_ attributes!
        self.groupdata._v_temps = None
        if "auto_group" in self.acl_users:
            self.acl_users.manage_delObjects(["auto_group"])

    def testWrapGroup(self):
        g = self.acl_users.getGroup("foo")
        self.assertEqual(g.__class__.__name__, "PloneGroup")
        g = self.groupdata.wrapGroup(g)
        self.assertEqual(g.__class__.__name__, "GroupData")
        self.assertEqual(aq_parent(g).__class__.__name__, "PloneGroup")
        self.assertEqual(aq_parent(aq_parent(g)).__class__.__name__, "GroupManager")


class TestGroupData(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.membership = self.portal.portal_membership
        self.memberdata = self.portal.portal_memberdata
        self.acl_users = self.portal.acl_users
        self.groups = self.portal.portal_groups
        self.groupdata = self.portal.portal_groupdata
        self.groups.addGroup("foo")
        if "auto_group" in self.acl_users:
            self.acl_users.manage_delObjects(["auto_group"])
        # MUST reset _v_ attributes!
        self.memberdata._v_temps = None
        self.groupdata._v_temps = None

    def testGetGroup(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(g.__class__.__name__, "GroupData")
        g = g.getGroup()
        self.assertEqual(g.__class__.__name__, "PloneGroup")

    def testGetTool(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(g.getTool().getId(), "portal_groupdata")

    def testGetGroupMembers(self):
        g = self.groups.getGroupById("foo")
        self.acl_users.userSetGroups(TEST_USER_ID, groupnames=["foo"])
        self.assertEqual(g.getGroupMembers()[0].getId(), TEST_USER_ID)

    def testGroupMembersAreWrapped(self):
        g = self.groups.getGroupById("foo")
        self.acl_users.userSetGroups(TEST_USER_ID, groupnames=["foo"])
        ms = g.getGroupMembers()
        self.assertEqual(ms[0].__class__.__name__, "MemberData")
        self.assertEqual(aq_parent(ms[0]).__class__.__name__, "PluggableAuthService")

    def testAddMember(self):
        self.portal.manage_role("Member", [Permissions.manage_users])
        g = self.groups.getGroupById("foo")
        g.addMember(TEST_USER_ID)
        self.assertEqual(g.getGroupMembers()[0].getId(), TEST_USER_ID)

    def testRemoveMember(self):
        self.portal.manage_role("Member", [Permissions.manage_users])
        g = self.groups.getGroupById("foo")
        g.addMember(TEST_USER_ID)
        g.removeMember(TEST_USER_ID)
        self.assertEqual(len(g.getGroupMembers()), 0)

    def testSetGroupProperties(self):
        g = self.groups.getGroupById("foo")
        g.setGroupProperties({"email": "foo@bar.com"})
        gd = self.groups.getGroupById("foo")
        self.assertEqual(gd.getProperty("email"), "foo@bar.com")

    def testSetMemberProperties(self):
        # For reference
        m = self.membership.getMemberById(TEST_USER_ID)
        m.setMemberProperties({"email": "foo@bar.com"})
        md = self.membership.getMemberById(TEST_USER_ID)
        self.assertEqual(md.getProperty("email"), "foo@bar.com")

    def testGetProperty(self):
        g = self.groups.getGroupById("foo")
        g.setGroupProperties({"email": "foo@bar.com"})
        self.assertEqual(g.getProperty("email"), "foo@bar.com")
        self.assertEqual(g.getProperty("id"), "foo")

    def testGetGroupName(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(g.getGroupName(), "foo")

    def testGetGroupId(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(g.getGroupId(), "foo")

    def testGetRoles(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(tuple(g.getRoles()), ("Authenticated",))
        self.groups.editGroup(g.getId(), roles=["Member"])
        g = self.groups.getGroupById("foo")
        self.assertEqual(sortTuple(tuple(g.getRoles())), ("Authenticated", "Member"))

    def testGetRolesInContext(self):
        self.folder = self.portal["folder"]
        g = self.groups.getGroupById("foo")
        self.acl_users.userSetGroups(TEST_USER_ID, groupnames=["foo"])
        user = self.acl_users.getUser(TEST_USER_NAME)
        self.assertEqual(
            user.getRolesInContext(self.folder).sort(),
            ["Member", "Authenticated", "Owner"].sort(),
        )
        self.folder.manage_setLocalRoles(g.getId(), ["NewRole"])
        self.assertEqual(
            user.getRolesInContext(self.folder).sort(),
            ["Member", "Authenticated", "Owner", "NewRole"].sort(),
        )

    def testGetDomains(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(g.getDomains(), ())

    def testHasRole(self):
        g = self.groups.getGroupById("foo")
        self.groups.editGroup(g.getId(), roles=["Member"])
        g = self.groups.getGroupById("foo")
        self.assertTrue(g.has_role("Member"))


class TestMethodProtection(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.groups = self.portal.portal_groups
        self.groups.addGroup("foo")
        self.groupdata = self.groups.getGroupById("foo")

    def testAnonAddMember(self):
        logout()
        self.assertRaises(Unauthorized, self.groupdata.addMember, TEST_USER_ID)

    def testAnonRemoveMember(self):
        logout()
        self.assertRaises(Unauthorized, self.groupdata.removeMember, TEST_USER_ID)

    def testMemberAddMember(self):
        self.assertRaises(Unauthorized, self.groupdata.addMember, TEST_USER_ID)

    def testMemberRemoveMember(self):
        self.assertRaises(Unauthorized, self.groupdata.removeMember, TEST_USER_ID)

    def testManagerAddMember(self):
        self.portal.manage_role("Member", [Permissions.manage_users])
        self.groupdata.addMember(TEST_USER_ID)

    def testManagerRemoveMember(self):
        self.portal.manage_role("Member", [Permissions.manage_users])
        self.groupdata.addMember(TEST_USER_ID)
        self.groupdata.removeMember(TEST_USER_ID)
