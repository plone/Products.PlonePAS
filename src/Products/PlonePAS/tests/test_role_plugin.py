# $Id$
"""Tests for Products.PlonePAS.plugins.role.GroupAwareRoleManager"""

from Products.PlonePAS.testing import PRODUCTS_PLONEPAS_INTEGRATION_TESTING
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.PluggableAuthService import _PLUGIN_TYPE_INFO
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.plugins.tests.helpers import DummyUser
from Products.PluggableAuthService.plugins.tests.helpers import FauxPAS
from Products.PluggableAuthService.plugins.tests.helpers import makeRequestAndResponse
from Products.PluginRegistry.PluginRegistry import PluginRegistry
from zope.interface import implementer

import unittest


@implementer(IGroupsPlugin)
class FauxGroupsPlugin(BasePlugin):
    def getGroupsForPrincipal(self, principal, request=None):
        return principal._groups


class GroupAwareRoleManagerTests(unittest.TestCase):
    """Roles manager that takes care of goup of principal"""

    layer = PRODUCTS_PLONEPAS_INTEGRATION_TESTING

    def _getTargetClass(self):

        from Products.PlonePAS.plugins.role import GroupAwareRoleManager

        return GroupAwareRoleManager

    def _makeOne(self, id="test", *args, **kw):

        plugin = self._getTargetClass()(id=id, *args, **kw)
        # We need to bind a fake request to this plugin
        request, dummy_response = makeRequestAndResponse()
        setattr(plugin, "REQUEST", request)
        return plugin

    def test_roles_for_control_panel(self):
        """There's a special case, the users control panel for which
        we should never grant to users the roles they have got through
        the groups they belong.
        In that intent, the control panels view pushes
        '__ignore_group_roles__' = True
        in the request.
        """
        root = FauxPAS()

        # Add a minimal PluginRegistry with a mock IGroupsPlugin, because the
        # roles plugin depends on it:
        root._setObject("plugins", PluginRegistry(_PLUGIN_TYPE_INFO))
        root._setObject("groups", FauxGroupsPlugin())
        root["plugins"].activatePlugin(IGroupsPlugin, "groups")

        garm = self._makeOne("garm").__of__(root)

        # 2 roles
        garm.addRole("foo_role")
        garm.addRole("bar_role")

        # Group 'somegroup' has 'bar_role'
        garm.assignRoleToPrincipal("bar_role", "somegroup")

        # 'johndoe' has 'foo_role'
        johndoe = DummyUser("johndoe", ("somegroup",))
        garm.assignRoleToPrincipal("foo_role", "johndoe")

        # 'johndoe' should have 'foo_role' and 'bar_roles'
        got = garm.getRolesForPrincipal(johndoe)
        expected = ["foo_role", "bar_role"]
        self.assertEqual(set(got), set(expected))

        # For the users control panel, johndoe has only the 'foo_role'
        garm.REQUEST.set("__ignore_group_roles__", True)
        got = garm.getRolesForPrincipal(johndoe)
        self.assertEqual(got, ("foo_role",))

        # Confirm we can get only the inherited roles
        garm.REQUEST.set("__ignore_group_roles__", False)
        garm.REQUEST.set("__ignore_direct_roles__", True)
        got = garm.getRolesForPrincipal(johndoe)
        self.assertEqual(got, ("bar_role",))

        return
