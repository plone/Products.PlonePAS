# -*- coding: utf-8 -*-
# $Id$
"""Tests for Products.PlonePAS.plugins.role.GroupAwareRoleManager"""

import unittest

from Products.PluggableAuthService.plugins.tests.test_ZODBRoleManager import ZODBRoleManagerTests
from Products.PluggableAuthService.plugins.tests.helpers import (
    FauxPAS, DummyUser, makeRequestAndResponse)


class GroupAwareRoleManagerTests(ZODBRoleManagerTests):
    """Roles manager that takes care of goup of principal"""

    # As we inherit from ZODBRoleManagerTests, all tests from this
    # class will be performed for GroupAwareRoleManager such we can see
    # potential regressions

    def _getTargetClass(self):

        from Products.PlonePAS.plugins.role import GroupAwareRoleManager
        return GroupAwareRoleManager

    def _makeOne(self, id='test', *args, **kw):

        plugin = self._getTargetClass()(id=id, *args, **kw)
        # We need to bind a fake request to this plugin
        request, dummy_response = makeRequestAndResponse()
        setattr(plugin, 'REQUEST', request)
        return plugin

    def test_roles_for_control_panel(self):
        """There's a special case, the users control panel for which
        we should never grant to users the roles they have got through
        the groups they belong.
        In that intent, the control panels view pushes '__ignore_group_roles__' = True
        in the request.
        """
        root = FauxPAS()
        garm = self._makeOne('garm').__of__(root)

        # 2 roles
        garm.addRole('foo_role')
        garm.addRole('bar_role')

        # Group 'somegroup' has 'bar_role'
        garm.assignRoleToPrincipal('bar_role', 'somegroup')

        # 'johndoe' has 'foo_role'
        johndoe = DummyUser('johndoe', ('somegroup',))
        garm.assignRoleToPrincipal('foo_role', 'johndoe')

        # 'johndoe' should have 'foo_role' and 'bar_roles'
        got = garm.getRolesForPrincipal(johndoe)
        expected = ['foo_role', 'bar_role']
        self.failUnlessEqual(set(got), set(expected))

        # For the users control panel, johndoe has only the 'foo_role'
        garm.REQUEST.set('__ignore_group_roles__', True)
        got = garm.getRolesForPrincipal(johndoe)
        self.failUnlessEqual(got, ('foo_role',))
        return


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(GroupAwareRoleManagerTests),))
