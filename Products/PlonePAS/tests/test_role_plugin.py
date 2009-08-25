# -*- coding: utf-8 -*-
# $Id$
"""Tests for Products.PlonePAS.plugins.role.GroupAwareRoleManager"""

import unittest
from zope.publisher.browser import TestRequest

from zExceptions import Forbidden

from Products.PluggableAuthService.tests.conformance import IRolesPlugin_conformance
from Products.PluggableAuthService.tests.conformance import IRoleEnumerationPlugin_conformance
from Products.PluggableAuthService.tests.conformance import IRoleAssignerPlugin_conformance

from Products.PluggableAuthService.plugins.tests.test_ZODBRoleManager import ZODBRoleManagerTests

from Products.PluggableAuthService.plugins.tests.helpers import (
    FauxPAS, FauxSmartPAS, DummyUser, makeRequestAndResponse)

REQUEST = TestRequest()

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

def test_suite():
    return unittest.TestSuite((unittest.makeSuite(GroupAwareRoleManagerTests),))
