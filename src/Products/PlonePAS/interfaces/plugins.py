from Products.PluggableAuthService.interfaces import plugins
from Products.PluggableAuthService.interfaces.plugins import Interface


class IUserIntrospection(Interface):
    """
    Introspect users in a user source, api users need to be careful as
    all sources may or not support this interface.

    Realistically this can only be done by authentication sources, or
    plugins which have intimate knowledge of such.
    """

    def getUserIds():
        """
        Return a list of user ids
        """

    def getUserNames():
        """
        Return a list of usernames
        """

    def getUsers():
        """
        Return a list of users
        """


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


class IMutablePropertiesPlugin(Interface):
    """
    Return a property set for a user. Property set can either an
    object conforming to the IMutable property sheet interface or a
    dictionary (in which case the properties are not persistently
    mutable).
    """

    def getPropertiesForUser(user, request=None):
        """
        User -> IMutablePropertySheet || {}

        o User will implement IPropertiedUser.

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present
        """

    def setPropertiesForUser(user, propertysheet):
        """
        Set modified properties on the user persistently.

        Raise a ValueError if the property or property value is invalid
        """

    def deleteUser(user_id):
        """
        Remove properties stored for a user
        """


class ISchemaMutablePropertiesPlugin(Interface):
    def addProperty(property_type, property_name, default=None):
        """
        Add a new property to a property provider.
        """
