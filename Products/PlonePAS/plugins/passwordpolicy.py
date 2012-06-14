"""
Password Validation plugin (IValidationPlugin)
Mutable Property Provider
"""
import copy

from zope.interface import implements
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from BTrees.OOBTree import OOBTree
from ZODB.PersistentMapping import PersistentMapping

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IValidationPlugin
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('plone')

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

manage_addPasswordPolicyForm = PageTemplateFile("../zmi/PasswordPolicyForm", globals())


def manage_addPasswordPolicyPlugin(self, id, title='',
                                          RESPONSE=None, schema=None, **kw):
    """
    Create an instance of a password validation plugin.
    """
    o = PasswordPolicyPlugin(id, title)
    self._setObject(o.getId(), o)

    if RESPONSE is not None:
        return RESPONSE.redirect("%s/manage_workspace?manage_tabs_message=DefaultPasswordPlugin+plugin+added" %
                self.absolute_url())

class PasswordPolicyPlugin(BasePlugin):
    """Simple Password Policy to ensure password is 5 chars long.
    """

    meta_type = 'Default Plone Password Policy'

    implements(IValidationPlugin)

    security = ClassSecurityInfo()

    def __init__(self, id, title=''):
        """Create a default plone password policy to ensure 5 char passwords
        """
        self.id = id
        self.title = title

    security.declarePrivate('validateUserInfo')
    def validateUserInfo(self, user, set_id, set_info ):
        """ See IValidationPlugin. Used to validate password property
        """

        if not set_info:
            return []
        password = set_info.get('password', None)
        if password is None:
            return []
        elif password == '':
            return [{'id':'password','error':_(u'Minimum 5 characters.')}]
        elif len(password) < 5:
            return [{'id':'password','error':
                _(u'Your password must contain at least 5 characters.')}]
        else:
            return []

InitializeClass(PasswordPolicyPlugin)

