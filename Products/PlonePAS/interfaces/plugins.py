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
$Id: plugins.py,v 1.3 2005/02/06 08:18:51 k_vertigo Exp $
"""

from Interface import Interface
from Products.PluggableAuthService.interfaces import plugins

class IUserIntrospection( Interface ):
    """
    introspect users in a user source, api users need to be
    careful as all sources may or not support this interface.
    """
    def getUserIds(self):
        """
        return a list of user ids
        """

    def getUserNames(self):
        """
        return a list of usernames
        """

    def getUsers(self):
        """
        return a list of users
        """

class ILocalRolesPlugin( Interface ):
    """
    plugin for determining a user's local roles and object access based on
    local roles.
    """
    
    def getRolesInContext( user, object):
        """
        Return the list of roles assigned to the user.

        o Include local roles assigned in context of the passed-in object.

        o Include *both* local roles assigned directly to us *and* those
          assigned to our groups.

        o Ripped off from AccessControl.User.BasicUser, which provides
          no other extension mechanism. :(
        """

    def checkLocalRolesAllowed( user, object, object_roles):
        """
        Check whether the user has access to object based
        on local roles. access is determined by a user's local roles
        including one of the object roles.
        """
    

class IUserManagement( plugins.IUserAdderPlugin ):

    """ Manage users 
    """

    def doChangeUser( login, password, **kw):
        """
        change a user's password ( differs from role )
        roles are set in the pas engine api for
        the same but are set via a role manager )
        """

    def doDeleteUser( login ):
        """
        Remove a user record from a User Manager, with the given login
        and password

        o Return a Boolean indicating whether a user was removed or not
        """
