"""

group interfaces for plone, based off existing group usage pre pas. 

$Id: group.py,v 1.2 2005/02/03 00:09:48 k_vertigo Exp $
"""

from Products.PluggableAuthService.interfaces import plugins
from Interface import Interface


class IGroupManagement(Interface):

    def addGroup(id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        """

    def addPrincipalToGroup(self, principal_id, group_id):
        """
        Add a given principal to the group.
        """

    def updateGroup(id, roles=(), **kw):
        """
        Edit the given group with the supplied roles.
        """

    def setRolesForGroup( group_id, roles=() ):
        """
        set roles for group
        """

    def removeGroup( group_id ):
        """
        Remove the given group
        """

    def removePrincipalFromGroup( principal_id, group_id ):
        """
        remove the given principal from the group
        """

class IGroupIntrospection(Interface):

    def getGroupById( group_id ):
        """
        Returns the portal_groupdata-ish object for a group
        corresponding to this id.
        """

    def searchGroups( **kw ):
        """
        return groups matching search criterion
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

    def getGroupMembers( group_id ):
        """
        return the members of the given group
        """

class IGroupSpaceManagement(Interface):

    def getGroupSpaceContainer(self):
        """
        return the group space container
        """

    def setGroupSpaceCreationFlag( flag ):
        """
        set the creation flag, ie. whether or not to create
        group spaces.
        """

    def getGroupSpaceForGroup( group_id ):
        """
        return the groupspace for the given group id
        """

    def getGroupSpaceURL( group_id ):
        """
        return the url to the groupspace for the given group
        """

    def createGroupSpace( group_id ):
        """
        create a groupspace for the given group id
        """


class IGroupDataTool( Interface ):

    def wrapGroup( group ):
        """
        decorate a group with property management capabilities if needed
        """

class IGroupTool( IGroupIntrospection,
                  IGroupManagement,
                  plugins.IGroupsPlugin,
                  IGroupSpaceManagement ):

    """
    Defines an interface for managing and introspecting and
    groups and group membership.
    """


