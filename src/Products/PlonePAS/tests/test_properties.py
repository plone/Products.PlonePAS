from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.plugins.property import ZODBMutablePropertyProvider
from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_INTEGRATION_TESTING
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin

import unittest


class PropertiesTest(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_user_properties(self):
        mt = getToolByName(self.portal, "portal_membership")
        md = getToolByName(self.portal, "portal_memberdata")

        # Create a new Member
        mt.addMember(
            "user1",
            "u1",
            ["Member"],
            [],
            {"email": "user1@host.com", "fullname": "User #1"},
        )
        member = mt.getMemberById("user1")
        self.assertFalse(member is None)

        # Assert user doesn't have the property yet
        self.assertFalse(member.hasProperty("age"))

        # Add new property
        md.manage_addProperty("age", 20, "int")

        # Assert user has the property now
        self.assertTrue(member.hasProperty("age"))

        # Get the property, should have the default value
        got = member.getProperty("age", None)
        expected = 20
        self.assertEqual(got, expected)

        # get a handle on the member
        member = mt.getMemberById("user1")

        # Set some member properties. Needs to be logged in as the user.
        login(self.portal, "user1")
        member.setMemberProperties(
            {"age": 30, "fullname": "User #1 Is Cool", "email": "user1@anotherhost.qa"}
        )

        # Check the properties have been set
        got = member.getProperty("age", None)
        expected = 30
        self.assertEqual(got, expected)

        got = member.getProperty("fullname", None)
        expected = "User #1 Is Cool"
        self.assertEqual(got, expected)

        got = member.getProperty("email", None)
        expected = "user1@anotherhost.qa"
        self.assertEqual(got, expected)

        # Delete the property
        md.manage_delProperties(ids=("age",))

        # re-get the member to reflect the new memberdata schema
        member = mt.getMemberById("user1")

        # Assert property is gone
        self.assertFalse(member.hasProperty("age"))

        # Get the property, should return default (None)
        got = member.getProperty("age", None)
        expected = None
        self.assertEqual(got, expected)

        # Other properties should still be there.
        got = member.getProperty("fullname", None)
        expected = "User #1 Is Cool"
        self.assertEqual(got, expected)

        got = member.getProperty("email", None)
        expected = "user1@anotherhost.qa"
        self.assertEqual(got, expected)

    def test_group_properties(self):
        gt = getToolByName(self.portal, "portal_groups")
        gd = getToolByName(self.portal, "portal_groupdata")

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        # Create a new Group
        gt.addGroup(
            "group1",
            ["Reviewer"],
            [],
            {"email": "group1@host.com", "title": "Group #1"},
        )
        group = gt.getGroupById("group1")
        self.assertFalse(group is None)

        # Assert group doesn't have the property yet
        self.assertFalse(group.hasProperty("karma"))

        # Add new property
        gd.manage_addProperty("karma", 20, "int")

        # get group again to re-create with new groupdata schema
        group = gt.getGroupById("group1")

        # Assert group has the property now
        self.assertTrue(group.hasProperty("karma"))

        # Get the property, should have the default value
        got = group.getProperty("karma", None)
        expected = 20

        self.assertEqual(got, expected)

        # Set some group properties
        group.setGroupProperties(
            {"karma": 30, "title": "Group #1 Is Cool", "email": "group1@anotherhost.qa"}
        )

        # Check the properties have been set
        got = group.getProperty("karma", None)
        expected = 30
        self.assertEqual(got, expected)

        got = group.getProperty("title", None)
        expected = "Group #1 Is Cool"
        self.assertEqual(got, expected)

        got = group.getProperty("email", None)
        expected = "group1@anotherhost.qa"
        self.assertEqual(got, expected)

        # Delete the property
        gd.manage_delProperties(ids=("karma",))

        # get group again to re-create with new groupdata schema
        group = gt.getGroupById("group1")

        # Assert property is gone
        self.assertFalse(group.hasProperty("karma"))

        # Get the property, should return default (None)
        got = group.getProperty("karma", None)
        expected = None
        self.assertEqual(got, expected)

        # Other properties should still be there.
        got = group.getProperty("title", None)
        expected = "Group #1 Is Cool"
        self.assertEqual(got, expected)

        got = group.getProperty("email", None)
        expected = "group1@anotherhost.qa"
        self.assertEqual(got, expected)

    def test_schema_for_mutable_property_provider(self):
        """Add a schema to a ZODBMutablePropertyProvider."""

        # Schema is list of tuples with name, type (string), value.
        # From the types it seems only 'lines' is handled differently.
        address_schema = [
            ("addresses", "lines", ["Here", "There"]),
            ("city", "str", "Somewhere"),
            ("telephone", "int", 1234567),
        ]

        # This used to give a ValueError, so we just check that it
        # does not.
        provider = ZODBMutablePropertyProvider(
            "address_plugin", "Address Plugin", schema=address_schema
        )

        # When this test passes, we are happy already, but let's add a
        # few more basic tests.

        # Create a new Member
        mt = getToolByName(self.portal, "portal_membership")
        mt.addMember(
            "user1",
            "u1",
            ["Member"],
            [],
            {"email": "user1@host.com", "fullname": "User #1"},
        )
        member = mt.getMemberById("user1")
        sheet = provider.getPropertiesForUser(member)
        self.assertEqual(sheet.propertyIds(), ["addresses", "city", "telephone"])
        self.assertEqual(
            sheet.propertyInfo("city"), {"type": "str", "id": "city", "mode": ""}
        )
        self.assertEqual(sheet.getProperty("addresses"), ("Here", "There"))


class PropertySearchTest(unittest.TestCase):

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.mt = getToolByName(self.portal, "portal_membership")
        self.md = getToolByName(self.portal, "portal_memberdata")
        self.gt = getToolByName(self.portal, "portal_groups")

        # Create a new Member
        self.mt.addMember(
            "member1",
            "pw",
            ["Member"],
            [],
            {"email": "member1@host.com", "title": "Member #1"},
        )
        member = self.mt.getMemberById("member1")
        self.assertFalse(member is None)

        self.mt.addMember(
            "member2",
            "pw",
            ["Member"],
            [],
            {"email": "user2@otherhost.com", "fullname": "User #2"},
        )
        member = self.mt.getMemberById("member2")
        self.assertFalse(member is None)

        # Add a Group to make sure searchUsers isn't returning them in results.
        self.gt.addGroup("group1", title="Group 1")
        group = self.gt.getGroupById("group1")
        self.assertFalse(group is None)

        self.pas = getToolByName(self.portal, "acl_users")
        for plugin in self.pas.plugins.getAllPlugins("IUserEnumerationPlugin")[
            "active"
        ]:
            if plugin != "mutable_properties":
                self.pas.plugins.deactivatePlugin(IUserEnumerationPlugin, plugin)

    def testPluginActivated(self):
        plugins = self.pas.plugins.getAllPlugins("IUserEnumerationPlugin")["active"]
        self.assertEqual(plugins, ("mutable_properties",))

    def testEmptySearch(self):
        results = self.pas.searchUsers()
        self.assertEqual(len(results), 2)

    def testInexactStringSearch(self):
        results = self.pas.searchUsers(email="something@somewhere.tld")
        self.assertEqual(results, ())

        results = self.pas.searchUsers(email="member1@host.com", exact_match=False)
        results = [info["userid"] for info in results]
        self.assertEqual(results, ["member1"])

        results = self.pas.searchUsers(email="@host.com", exact_match=False)
        results = [info["userid"] for info in results]
        self.assertEqual(results, ["member1"])

        results = self.pas.searchUsers(email="member1@host.com", exact_match=True)
        results = [info["userid"] for info in results]
        self.assertEqual(results, ["member1"])

        results = self.pas.searchUsers(email="@host.com", exact_match=True)
        results = [info["userid"] for info in results]
        self.assertEqual(results, [])

    def testBooleanSearch(self):
        results = self.pas.searchUsers(visible_ids=True)
        results = [info["userid"] for info in results]
        self.assertEqual(results, [])

        results = self.pas.searchUsers(visible_ids=False)
        results = [info["userid"] for info in results]
        self.assertEqual(results, ["member1", "member2"])

    def testGroupsNotReturnedByEnumerateUsers(self):
        """Check to make sure that groups aren't returned by a enumerateUsers
        call.
        See http://dev.plone.org/plone/ticket/9435"""
        results = self.pas.searchUsers()
        resultIds = [a["id"] for a in results]
        self.assertFalse("group1" in resultIds)

    def testSearchEmptyId(self):
        self.assertEqual(self.pas.mutable_properties.enumerateUsers(id=""), ())
        self.assertEqual(self.pas.mutable_properties.enumerateUsers(login=""), ())

    def testCantSearchByIdOrLogin(self):
        # we can't search by id
        results = self.pas.searchUsers(id="member1")
        self.assertEqual(results, ())
        # or login
        results = self.pas.searchUsers(login="member1")
        self.assertEqual(results, ())
