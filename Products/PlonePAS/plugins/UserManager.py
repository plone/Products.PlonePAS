##############################################################################
#
# Copyright (c) 2005 Plone Foundation
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

$Id: UserManager.py,v 1.2 2005/02/06 08:18:52 k_vertigo Exp $
"""

from AccessControl import ClassSecurityInfo, AuthEncoding
from Globals import InitializeClass, DTMLFile

from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PluggableAuthService.plugins.ZODBUserManager \
     import ZODBUserManager as BasePlugin

manage_addUserManagerForm = DTMLFile('../zmi/UserManagerForm',
                                          globals())

def manage_addUserManager( dispatcher, id, title=None, REQUEST=None ):
    """ Add a UserManager to a Pluggable Auth Service. """

    pum = UserManager(id, title)
    dispatcher._setObject(pum.getId(), pum)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
                                '%s/manage_workspace'
                                '?manage_tabs_message='
                                'UserManager+added.'
                            % dispatcher.absolute_url())

class UserManager( BasePlugin ):
    """ PAS plugin for managing users. (adds write API) """

    meta_type = 'User Manager'
    __implements__ = BasePlugin.__implements__ + (IUserManagement,)
    
    security = ClassSecurityInfo()

    security.declarePrivate('doDeleteUser')
    def doDeleteUser(self, login):
        """ given a login, delete a user """
        self.removeUser(login)

    security.declarePrivate('doChangeUser')
    def doChangeUser(self, principal_id, password ):
        """ change a user's password """
        if self._user_passwords.get(principal_id) is None:
            raise RuntimeError("user does not exist %s"%principal_id)
        self._user_passwords[principal_id] = AuthEncoding.pw_encrypt( password )


InitializeClass( UserManager )
