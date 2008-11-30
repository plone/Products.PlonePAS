from zope.interface import Interface
from Products.PluggableAuthService.interfaces import plugins


class IGroupManagement(Interface):

    def addGroup(id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        return True if the operation suceeded
        """

    def addPrincipalToGroup(self, principal_id, group_id):
        """
        Add a given principal to the group.
        return True on success
        """

    def updateGroup(id, **kw):
        """
        Edit the given group. plugin specific
        return True on success
        """

    def setRolesForGroup(group_id, roles=()):
        """
        set roles for group
        return True on success
        """

    def removeGroup(group_id):
        """
        Remove the given group
        return True on success
        """

    def removePrincipalFromGroup(principal_id, group_id):
        """
        remove the given principal from the group
        return True on success
        """

class IGroupIntrospection(Interface):

    def getGroupById(group_id):
        """
        Returns the portal_groupdata-ish object for a group
        corresponding to this id.
        """

    #################################
    # these interface methods are suspect for scalability.
    #################################

    def getGroups():
        """
        Returns an iteration of the available groups
        """

    def getGroupIds():
        """
        Returns a list of the available groups
        """

    def getGroupMembers(group_id):
        """
        return the members of the given group
        """


class IGroupDataTool(Interface):

    def wrapGroup(group):
        """
        decorate a group with property management capabilities if needed
        """

class IGroupTool(IGroupIntrospection,
                  IGroupManagement,
                  plugins.IGroupsPlugin):

    """
    Defines an interface for managing and introspecting and
    groups and group membership.
    """


class IGroupData(Interface):
    """ An abstract interface for accessing properties on a group object"""

    def setProperties(properties=None, **kw):
        """Allows setting of group properties en masse.
        Properties can be given either as a dict or a keyword parameters list"""

    def getProperty(id):
        """ Return the value of the property specified by 'id' """

    def getProperties():
        """ Return the properties of this group. Properties are as usual in Zope."""

    def getGroupId():
        """ Return the string id of this group, WITHOUT group prefix."""

    def getMemberId():
        """This exists only for a basic user/group API compatibility
        """

    def getGroupName():
        """ Return the name of the group."""

    def getGroupMembers():
        """ Return a list of the portal_memberdata-ish members of the group."""

    def getAllGroupMembers():
        """ Return a list of the portal_memberdata-ish members of the group
        including transitive ones (ie. users or groups of a group in that group)."""

    def getGroupMemberIds():
        """ Return a list of the user ids of the group."""

    def getAllGroupMemberIds():
        """ Return a list of the user ids of the group.
        including transitive ones (ie. users or groups of a group in that group)."""

    def addMember(id):
        """ Add the existing member with the given id to the group"""

    def removeMember(id):
        """ Remove the member with the provided id from the group """

    def getGroup():
        """ Returns the actual group implementation. Varies by group
        implementation (GRUF/Nux/et al)."""
