from AccessControl import Permissions
from AccessControl import Unauthorized
from Acquisition import aq_base
from Acquisition import aq_parent
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.plugins.group import PloneGroup
from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_INTEGRATION_TESTING
from Products.PlonePAS.tools.groupdata import GroupData
from Products.PluggableAuthService.interfaces.events import IGroupDeletedEvent
from zope.component import adapter
from zope.component import getGlobalSiteManager

import unittest


def sortTuple(t):
    l = list(t)
    l.sort()
    return tuple(l)


class TestGroupsTool(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.gt = getToolByName(self.portal, "portal_groups")
        self.gd = getToolByName(self.portal, "portal_groupdata")

        self.group_id = "group1"
        # Create a new Group
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.gt.addGroup(
            self.group_id,
            ["Reviewer"],
            [],
            {"email": "group1@host.com", "title": "Group #1"},
        )

    def test_get_group(self):
        # Use PAS (monkeypatched) API method to get a group by id.
        group = self.portal.acl_users.getGroup(self.group_id)
        self.assertFalse(group is None)

        # Should be wrapped into the GroupManagement, which is wrapped
        # into the PAS.
        got = aq_base(aq_parent(aq_parent(group)))
        expected = aq_base(self.portal.acl_users)
        self.assertEqual(got, expected)

        self.assertTrue(isinstance(group, PloneGroup))

    def test_get_group_by_id(self):
        # Use tool way of getting group by id. This returns a
        # GroupData object wrapped by the group
        group = self.gt.getGroupById(self.group_id)
        self.assertFalse(group is None)
        self.assertTrue(isinstance(group, GroupData))
        self.assertTrue(isinstance(aq_parent(group), PloneGroup))

    def test_edit_group(self):
        # Use the tool way to edit a group.
        properties = {"email": "group1@host2.com", "title": "Group #1 new title"}
        self.gt.editGroup(self.group_id, roles=["Manager"], **properties)

        # test edition of roles and properties
        group = self.gt.getGroupById(self.group_id)
        self.assertTrue(group.has_role("Manager"))
        self.assertEqual(group.getProperty("email"), properties["email"])
        self.assertEqual(group.getProperty("title"), properties["title"])

        # test for empty list of roles
        self.gt.editGroup(self.group_id, roles=[])
        self.assertTrue(group.has_role("Authenticated"))

        # test edition of group groups
        self.gt.editGroup(self.group_id, groups=["Reviewers"], **properties)
        group = self.gt.getGroupById(self.group_id)
        self.assertTrue("Reviewers" in group.getGroups())


class TestMethodProtection(unittest.TestCase):
    # GroupData has wrong security declarations

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


class TestGroupsToolIntegration(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.membership = self.portal.portal_membership
        self.acl_users = self.portal.acl_users
        self.groups = self.portal.portal_groups
        self.folder = self.portal["folder"]

        if "auto_group" in self.acl_users:
            self.acl_users.manage_delObjects(["auto_group"])

        # Nuke Administators and Reviewers groups added in 2.1a2 migrations
        # (and any other migrated-in groups) to avoid test confusion
        self.groups.removeGroups(self.groups.listGroupIds())

    def testAddGroup(self):
        self.groups.addGroup("foo", [], [])
        self.assertEqual(self.groups.listGroupIds(), ["foo"])

    def testGetGroupById(self):
        self.groups.addGroup("foo", [], [])
        g = self.groups.getGroupById("foo")
        self.assertNotEqual(g, None)

    def testGetBadGroupById(self):
        g = self.groups.getGroupById("foo")
        self.assertEqual(g, None)

    def testGroupByIdIsWrapped(self):
        self.groups.addGroup("foo", [], [])
        g = self.groups.getGroupById("foo")
        self.assertEqual(g.__class__.__name__, "GroupData")
        self.assertEqual(aq_parent(g).__class__.__name__, "PloneGroup")
        self.assertEqual(aq_parent(aq_parent(g)).__class__.__name__, "GroupManager")

    def testEditGroup(self):
        self.groups.addGroup(
            "foo",
        )
        self.groups.editGroup("foo", roles=["Reviewer"])
        g = self.groups.getGroupById("foo")
        self.assertEqual(sortTuple(g.getRoles()), ("Authenticated", "Reviewer"))

    def testEditBadGroup(self):
        # Error type depends on the user folder...
        try:
            self.groups.editGroup("foo", [], [])
        except (KeyError, ValueError):
            pass  # Ok, this is the wanted behaviour
        else:
            self.fail("Should have raised KeyError or ValueError")

    def testRemoveGroups(self):
        self.groups.addGroup("foo", [], [])
        self.groups.removeGroups(["foo"])
        self.assertEqual(len(self.groups.listGroupIds()), 0)

    def testRemoveGroupDelEvent(self):
        eventsFired = []

        @adapter(IGroupDeletedEvent)
        def gotDeletion(event):
            eventsFired.append(event)

        gsm = getGlobalSiteManager()
        gsm.registerHandler(gotDeletion)
        self.groups.addGroup("foo", [], [])
        self.groups.removeGroups(["foo"])
        self.assertEqual(len(eventsFired), 1)
        self.assertEqual(eventsFired[0].principal, "foo")
        gsm.unregisterHandler(gotDeletion)

    def testListGroupIds(self):
        self.groups.addGroup("foo", [], [])
        self.groups.addGroup("bar", [], [])
        grps = self.groups.listGroupIds()
        grps.sort()
        self.assertEqual(grps, ["bar", "foo"])

    def testGetGroupsByUserId(self):
        self.groups.addGroup("foo", [], [])
        self.acl_users.userSetGroups(TEST_USER_ID, groupnames=["foo"])
        gs = self.groups.getGroupsByUserId(TEST_USER_ID)
        self.assertEqual(gs[0].getId(), "foo")

    def testGroupsByUserIdAreWrapped(self):
        self.groups.addGroup("foo", [], [])
        self.acl_users.userSetGroups(TEST_USER_ID, groupnames=["foo"])
        gs = self.groups.getGroupsByUserId(TEST_USER_ID)
        self.assertEqual(gs[0].__class__.__name__, "GroupData")
        self.assertEqual(aq_parent(gs[0]).__class__.__name__, "PloneGroup")
        self.assertEqual(aq_parent(aq_parent(gs[0])).__class__.__name__, "GroupManager")

    def testListGroups(self):
        self.groups.addGroup("foo", [], [])
        self.groups.addGroup("bar", [], [])
        gs = self.groups.listGroups()
        self.assertEqual(gs[0].getId(), "bar")
        self.assertEqual(gs[1].getId(), "foo")

    def testListedGroupsAreWrapped(self):
        self.groups.addGroup("foo", [], [])
        gs = self.groups.listGroups()
        self.assertEqual(gs[0].__class__.__name__, "GroupData")
        self.assertEqual(aq_parent(gs[0]).__class__.__name__, "PloneGroup")
        self.assertEqual(aq_parent(aq_parent(gs[0])).__class__.__name__, "GroupManager")

    def testSetGroupOwnership(self):
        self.groups.addGroup("foo", [], [])
        self.folder.invokeFactory("Document", "doc")
        doc = self.folder.doc
        g = self.groups.getGroupById("foo")
        self.groups.setGroupOwnership(g, doc)
        self.assertEqual(doc.getOwnerTuple()[1], "foo")
        self.assertEqual(doc.get_local_roles_for_userid("foo"), ("Owner",))
        self.assertEqual(doc.get_local_roles_for_userid(TEST_USER_ID), ("Owner",))

    def testWrapGroup(self):
        self.groups.addGroup("foo", [], [])
        g = self.acl_users.getGroup("foo")
        self.assertEqual(g.__class__.__name__, "PloneGroup")
        g = self.groups.wrapGroup(g)
        self.assertEqual(g.__class__.__name__, "GroupData")
        self.assertEqual(aq_parent(g).__class__.__name__, "PloneGroup")
        self.assertEqual(aq_parent(aq_parent(g)).__class__.__name__, "GroupManager")

    def testGetGroupInfo(self):
        self.groups.addGroup("foo", title="Foo", description="Bar", email="foo@foo.com")
        info = self.groups.getGroupInfo("foo")
        self.assertEqual(info.get("title"), "Foo")
        self.assertEqual(info.get("description"), "Bar")
        self.assertEqual(info.get("email"), None)  # No email!

    def testGetGroupInfoAsAnonymous(self):
        self.groups.addGroup("foo", title="Foo", description="Bar")
        logout()
        info = self.groups.restrictedTraverse("getGroupInfo")("foo")
        self.assertEqual(info.get("title"), "Foo")
        self.assertEqual(info.get("description"), "Bar")

    def testGetBadGroupInfo(self):
        info = self.groups.getGroupInfo("foo")
        self.assertEqual(info, None)
