# -*- coding: utf-8 -*-
from Products.PluggableAuthService.interfaces import plugins
from Products.PluggableAuthService.interfaces.plugins import Interface
from zope.deferredimport import deprecated


deprecated(
    "Import from Products.PluggableAuthService.interfaces.plugins instead",
    IUserIntrospection="Products.PluggableAuthService.interfaces.plugins:"
                       "IUserIntrospection",
)


class ILocalRolesPlugin(Interface):
    """
    Plugin for determining a user's local roles and object access
    based on local roles.
    """

    def getRolesInContext(user, object):
        """
        Return the list of roles assigned to the user.

        o Include local roles assigned in context of the passed-in object.

        o Include *both* local roles assigned directly to us *and* those
          assigned to our groups.

        o Ripped off from AccessControl.User.BasicUser, which provides
          no other extension mechanism. :(
        """

    def checkLocalRolesAllowed(user, object, object_roles):
        """
        Check whether the user has access to object based
        on local roles. access is determined by a user's local roles
        including one of the object roles.
        """

    def getAllLocalRolesInContext(object):
        """
        Return active all local roles in a context.

        The roles are returned in a dictionary mapping a principal (a
        user or a group) to the set of roles assigned to it.
        """


class IUserManagement(plugins.IUserAdderPlugin):
    """
    Manage users
    """

    def doChangeUser(user_id, password, **kw):
        """
        Change a user's password (differs from role) roles are set in
        the pas engine api for the same but are set via a role
        manager)
        """

    def doDeleteUser(login):
        """
        Remove a user record from a User Manager, with the given login
        and password

        o Return a Boolean indicating whether a user was removed or
          not
        """


deprecated(
    'IMutablePropertiesPlugin moved to PluggableAuthService',
    IMutablePropertiesPlugin='Products.PluggableAuthService.interfaces.'
                             'plugins.IMutablePropertiesPlugin'
)

deprecated(
    'ISchemaMutablePropertiesPlugin moved to PluggableAuthService',
    ISchemaMutablePropertiesPlugin='Products.PluggableAuthService.interfaces.'
                                   'plugins.ISchemaMutablePropertiesPlugin'
)
