""" Class: ExtendedCookieAuthHelper

Simply extends the standard CookieAuthHelper provided via regular
PluggableAuthService but overrides the updateCookie mechanism to
provide similar functionality as CookieCrumbler does... by giving
the portal the ability to provide a setAuthCookie method.

$Id$
"""

from base64 import encodestring
from Acquisition import aq_base
from AccessControl.SecurityInfo import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile
from Products.PluggableAuthService.plugins.CookieAuthHelper \
    import CookieAuthHelper as BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.plugins import \
        ILoginPasswordHostExtractionPlugin, IChallengePlugin,  \
        ICredentialsUpdatePlugin, ICredentialsResetPlugin

from Products.CMFPlone.utils import log


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

manage_addExtendedCookieAuthHelperForm = DTMLFile("../zmi/ExtendedCookieAuthHelperForm", globals())



class ExtendedCookieAuthHelper(BasePlugin):
    """Multi-plugin which adds ability to override the updating of cookie via
    a setAuthCookie method/script.
    """
    
    meta_type = 'Extended Cookie Auth Helper'
    security = ClassSecurityInfo()
        
    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """Override standard updateCredentials method
        """
        
        setAuthCookie = getattr(self, 'setAuthCookie', None)
        if setAuthCookie:
            cookie_val = encodestring('%s:%s' % (login, new_password))
            cookie_val = cookie_val.rstrip()
            setAuthCookie(response, self.cookie_name, cookie_val)
        else:
            BasePlugin.updateCredentials(self, request, response, login, new_password)
    


classImplements(ExtendedCookieAuthHelper, 
                ILoginPasswordHostExtractionPlugin,
                IChallengePlugin,
                ICredentialsUpdatePlugin,
                ICredentialsResetPlugin,
               )

InitializeClass(ExtendedCookieAuthHelper)
