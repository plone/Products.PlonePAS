""" Class: ExtendedCookieAuthHelper

Simply extends the standard CookieAuthHelper provided via regular
PluggableAuthService but overrides the updateCookie mechanism to
provide similar functionality as CookieCrumbler does... by giving
the portal the ability to provide a setAuthCookie method.
"""

from base64 import encodestring
from urllib import quote

from zope.interface import implements

from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.PluggableAuthService.plugins.CookieAuthHelper \
    import CookieAuthHelper as BasePlugin
from Products.PluggableAuthService.interfaces.authservice \
        import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import \
        ILoginPasswordHostExtractionPlugin, IChallengePlugin,  \
        ICredentialsUpdatePlugin, ICredentialsResetPlugin


def manage_addExtendedCookieAuthHelper(self, id, title='',
                                       RESPONSE=None, **kw):
    """Create an instance of a extended cookie auth helper.
    """

    self = self.this()

    o = ExtendedCookieAuthHelper(id, title, **kw)
    self._setObject(o.getId(), o)
    o = getattr(aq_base(self), id)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addExtendedCookieAuthHelperForm = \
    DTMLFile("../zmi/ExtendedCookieAuthHelperForm", globals())


class ExtendedCookieAuthHelper(BasePlugin):
    """Multi-plugin which adds ability to override the updating of cookie via
    a setAuthCookie method/script.
    """

    meta_type = 'Extended Cookie Auth Helper'
    security = ClassSecurityInfo()

    implements(ILoginPasswordHostExtractionPlugin, IChallengePlugin,
               ICredentialsUpdatePlugin, ICredentialsResetPlugin)

    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """Override standard updateCredentials method
        """

        setAuthCookie = getattr(self, 'setAuthCookie', None)
        if setAuthCookie:
            cookie_val = encodestring('%s:%s' % (login, new_password))
            cookie_val = cookie_val.rstrip()
            setAuthCookie(response, self.cookie_name, quote(cookie_val))
        else:
            BasePlugin.updateCredentials(self, request, response, login,
                                         new_password)

    security.declarePublic('login')
    def login(self):
        """Set a cookie and redirect to the url that we tried to
        authenticate against originally.

        Override standard login method to avoid calling
        'return response.redirect(came_from)' as there is additional
        processing to ignore known bad come_from templates at
        login_next.cpy script.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        password = request.get('__ac_password', '')

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
                pas_instance.updateCredentials(request, response, login,
                                               password)


InitializeClass(ExtendedCookieAuthHelper)
