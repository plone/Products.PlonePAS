# -*- coding: utf-8 -*-
from plone.testing import zope
from Products.PlonePAS import testing
from Products.PluggableAuthService.interfaces import plugins as plugins_ifaces
from Products.PluggableAuthService.plugins import HTTPBasicAuthHelper

import unittest


class PortalSetupTest(unittest.TestCase):

    layer = testing.PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING

    def setUp(self):
        """
        Set up convenience references to test fixture from the layer.
        """
        self.app = self.layer["app"]
        self.root_acl_users = self.app.acl_users

    def test_zope_root_default_challenge(self):
        """
        The Zope root `/acl_users` default challenge plugin works.
        """
        # Check the Zope root PAS plugin configuration
        self.assertIn(
            "credentials_basic_auth",
            self.root_acl_users.objectIds(),
            "Basic auth plugin missing from Zope root `/acl_users`",
        )
        basic_plugin = self.root_acl_users.credentials_basic_auth
        self.assertIsInstance(
            basic_plugin,
            HTTPBasicAuthHelper.HTTPBasicAuthHelper,
            "Wrong Zope root `/acl_users` basic auth plugin type",
        )
        challenge_plugins = self.root_acl_users.plugins.listPlugins(
            plugins_ifaces.IChallengePlugin,
        )
        _, default_challenge_plugin = challenge_plugins[0]
        self.assertEqual(
            "/".join(default_challenge_plugin.getPhysicalPath()),
            "/".join(basic_plugin.getPhysicalPath()),
            "Wrong Zope root `/acl_users` default challenge plugin",
        )

        # Check the challenge response in the actual browser
        browser = zope.Browser(self.app)
        browser.raiseHttpErrors = False
        browser.open(self.app.absolute_url() + "/manage_main")
        self.assertEqual(
            browser.headers["Status"].lower(),
            "401 unauthorized",
            "Wrong Zope root `/acl_users` default challenge response status",
        )
