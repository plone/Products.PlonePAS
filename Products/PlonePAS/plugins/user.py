##############################################################################
#
# Copyright (c) 2005 Kapil Thangavelu
# Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
ZODB based user manager with introspection and management interfaces.

$Id: user.py,v 1.5 2005/05/25 14:47:21 dreamcatcher Exp $
"""

from AccessControl import ClassSecurityInfo, AuthEncoding
from Globals import InitializeClass, DTMLFile

from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PluggableAuthService.utils import createViewName
from Products.PluggableAuthService.plugins.ZODBUserManager \
     import ZODBUserManager as BasePlugin

manage_addUserManagerForm = DTMLFile('../zmi/UserManagerForm',
                                          globals())

def manage_addUserManager(dispatcher, id, title=None, REQUEST=None):
    """ Add a UserManager to a Pluggable Auth Service. """

    pum = UserManager(id, title)
    dispatcher._setObject(pum.getId(), pum)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
            '%s/manage_workspace'
            '?manage_tabs_message='
            'UserManager+added.'
            % dispatcher.absolute_url())

class UserManager(BasePlugin):
    """PAS plugin for managing users. (adds write API)
    """

    meta_type = 'User Manager'
    __implements__ = BasePlugin.__implements__ + (IUserManagement,)

    security = ClassSecurityInfo()

    def addUser(self, user_id, login_name, password):
        """Original ZODBUserManager.addUser, modified to check if
        incoming password is already encypted.

        This support clean migration from default user source.
        Should go into PAS.
        """
        if self._user_passwords.get(user_id) is not None:
            raise KeyError, 'Duplicate user ID: %s' % user_id

        if self._login_to_userid.get(login_name) is not None:
            raise KeyError, 'Duplicate login name: %s' % login_name

        if not AuthEncoding.is_encrypted(password):
            password = AuthEncoding.pw_encrypt(password)
        self._user_passwords[ user_id ] = password
        self._login_to_userid[ login_name ] = user_id
        self._userid_to_login[ user_id ] = login_name

        # enumerateUsers return value has changed
        view_name = createViewName('enumerateUsers')
        self.ZCacheable_invalidate(view_name=view_name)

    security.declarePrivate('doDeleteUser')
    def doDeleteUser(self, userid):
        """Given a user id, delete that user
        """
        return self.removeUser(userid)

    security.declarePrivate('doChangeUser')
    def doChangeUser(self, principal_id, password):
        """Change a user's password
        """
        if self._user_passwords.get(principal_id) is None:
            raise RuntimeError, "User does not exist: %s" % principal_id
        self._user_passwords[principal_id] = AuthEncoding.pw_encrypt(password)

InitializeClass(UserManager)
