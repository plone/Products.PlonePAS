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
$Id: plugins.py,v 1.5 2005/02/24 15:13:33 k_vertigo Exp $
"""

from Interface import Interface
from Products.PluggableAuthService.interfaces import plugins

class IUserIntrospection( Interface ):
    """
    introspect users in a user source, api users need to be
    careful as all sources may or not support this interface.

    realistically this can only be done by authentication sources,
    or plugins which have intimate knowledge of such.
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

    """
    Manage users 
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


class IMutablePropertiesPlugin( Interface ):

    """
    return a property set for a user. property set can either an object
    conforming to the imutable property sheet interface or a dictionary
    (in which case the properties are not persistently mutable ).
    """

    def getPropertiesForUser( user, request=None ):
        """
        user -> IMutablePropertySheet || {}
        
        o User will implement IPropertiedUser.

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present        
        """

    def setPropertiesForUser( user, propertysheet ):
        """
        set modified properties on the user persistently.

        raise a ValueError if the property or property value is invalid
        """


class ISchemaMutablePropertiesPlugin( Interface ):

    def addProperty( property_type, property_name, default=None ):
        """
        add a new property to a property provider.
        """

