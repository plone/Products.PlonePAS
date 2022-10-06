"""
Test set up specific to Plone through thea GenericSetup profile installation.
"""

from plone.app import testing as pa_testing
from plone.testing import zope
from Products.PlonePAS import testing
from Products.PluggableAuthService.interfaces import plugins as plugins_ifaces
from Products.PluggableAuthService.plugins import CookieAuthHelper
from Products.PluggableAuthService.plugins import HTTPBasicAuthHelper
from zope.component import hooks

import transaction
import unittest
import urllib.parse


class PortalSetupTest(unittest.TestCase):
    """
    Test set up specific to Plone through thea GenericSetup profile installation.
    """

    layer = testing.PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING

    def setUp(self):
        """
        Set up convenience references to test fixture from the layer.
        """
        self.app = self.layer["app"]
        self.root_acl_users = self.app.acl_users
        self.portal = self.layer["portal"]

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

    def test_zope_root_cookie_login(self):
        """
        The Zope root `/acl_users` cookie login works.
        """
        # Install the GenericSetup profile that performs the actual switch
        pa_testing.applyProfile(self.portal, "Products.PlonePAS:root-cookie")
        transaction.commit()

        # Make the cookie plugin the default auth challenge
        self.assertIn(
            "credentials_cookie_auth",
            self.root_acl_users.objectIds(),
            "Cookie auth plugin missing from Zope root `/acl_users`",
        )
        cookie_plugin = self.root_acl_users.credentials_cookie_auth
        self.assertIs(
            type(cookie_plugin.aq_base),
            CookieAuthHelper.CookieAuthHelper,
            "Wrong Zope root `/acl_users` cookie auth plugin type",
        )
        challenge_plugins = self.root_acl_users.plugins.listPlugins(
            plugins_ifaces.IChallengePlugin,
        )
        _, default_challenge_plugin = challenge_plugins[0]
        self.assertEqual(
            "/".join(default_challenge_plugin.getPhysicalPath()),
            "/".join(cookie_plugin.getPhysicalPath()),
            "Wrong Zope root `/acl_users` default challenge plugin",
        )

        # Check the challenge response in the actual browser
        browser = zope.Browser(self.app)
        browser.open(self.app.absolute_url() + "/manage_main")
        self.assertEqual(
            browser.headers["Status"].lower(),
            "200 ok",
            "Wrong Zope root `/acl_users` cookie challenge response status",
        )
        login_form_url = urllib.parse.urlsplit(browser.url)
        self.assertEqual(
            login_form_url._replace(query="").geturl(),
            cookie_plugin.absolute_url() + "/login_form",
            "Wrong Zope root `/acl_users` cookie challenge redirect",
        )

        # Workaround the fact that the `zope.component` site is still the Plone portal
        # when the test browser handles requests.
        hooks.setSite(None)
        zope.login(self.root_acl_users, pa_testing.SITE_OWNER_NAME)
        self.app.REQUEST.form["__ac_name"] = pa_testing.SITE_OWNER_NAME
        self.app.REQUEST.form["__ac_password"] = pa_testing.SITE_OWNER_PASSWORD
        cookie_plugin.login()

        # Submit the login form in the browser
        login_form = browser.getForm()
        login_form.getControl(name="__ac_name").value = pa_testing.SITE_OWNER_NAME
        login_form.getControl(
            name="__ac_password"
        ).value = pa_testing.SITE_OWNER_PASSWORD
        login_form.controls[-1].click()
        self.assertEqual(
            browser.headers["Status"].lower(),
            "200 ok",
            "Wrong Zope root `/acl_users` cookie login response status",
        )
        self.assertEqual(
            browser.url,
            self.app.absolute_url() + "/manage_main",
            "Wrong Zope root `/acl_users` cookie login redirect",
        )
