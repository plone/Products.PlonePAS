""" Class: ExtendedCookieAuthHelper

Simply extends the standard CookieAuthHelper provided via regular
PluggableAuthService but overrides the updateCookie mechanism to
provide similar functionality as CookieCrumbler does... by giving
the portal the ability to provide a setAuthCookie method.
"""
from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from DateTime import DateTime
from plone.registry.interfaces import IRegistry
from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin
from Products.PluggableAuthService.interfaces.plugins import (
    ILoginPasswordHostExtractionPlugin,
)
from Products.PluggableAuthService.plugins.CookieAuthHelper import (
    CookieAuthHelper as BasePlugin,
)
from urllib.parse import quote
from zope.component import getUtility
from zope.interface import implementer


def manage_addExtendedCookieAuthHelper(self, id, title="", RESPONSE=None, **kw):
    """Create an instance of a extended cookie auth helper."""

    self = self.this()

    o = ExtendedCookieAuthHelper(id, title, **kw)
    self._setObject(o.getId(), o)
    o = getattr(aq_base(self), id)

    if RESPONSE is not None:
        RESPONSE.redirect("manage_workspace")


manage_addExtendedCookieAuthHelperForm = DTMLFile(
    "../zmi/ExtendedCookieAuthHelperForm", globals()
)


@implementer(
    ILoginPasswordHostExtractionPlugin,
    IChallengePlugin,
    ICredentialsUpdatePlugin,
    ICredentialsResetPlugin,
)
class ExtendedCookieAuthHelper(BasePlugin):
    """Multi-plugin which adds ability to override the updating of cookie via
    a setAuthCookie method/script.
    """

    meta_type = "Extended Cookie Auth Helper"
    security = ClassSecurityInfo()

    @security.private
    def updateCredentials(self, request, response, login, new_password):
        """Override standard updateCredentials method"""
        cookie_val = self.get_cookie_value(login, new_password)
        kw = {}
        registry = getUtility(IRegistry)
        length = registry.get("plone.auth_cookie_length", "0")
        try:
            length = int(length)
        except ValueError:
            length = 0
        if length:
            kw.update(expires=(DateTime() + length).toZone("GMT").rfc822())
        response.setCookie(self.cookie_name, quote(cookie_val), path="/", **kw)

    @security.public
    def login(self):
        """Set a cookie and redirect to the url that we tried to
        authenticate against originally.

        Override standard login method to avoid calling
        'return response.redirect(came_from)' as there is additional
        processing to ignore known bad come_from templates at
        login_next.cpy script.
        """
        request = self.REQUEST
        response = request["RESPONSE"]

        password = request.get("__ac_password", "")

        user = getSecurityManager().getUser()
        login = user.getUserName()
        user_pas = aq_parent(user)

        if IPluggableAuthService.providedBy(user_pas):
            # Delegate to the users own PAS if possible
            user_pas.updateCredentials(request, response, login, password)
        else:
            # User does not originate from a PAS user folder, so lets try
            # to do our own thing.
            # XXX Perhaps we should do nothing here; test with pure User
            # Folder!
            pas_instance = self._getPAS()
            if pas_instance is not None:
                pas_instance.updateCredentials(request, response, login, password)


InitializeClass(ExtendedCookieAuthHelper)
