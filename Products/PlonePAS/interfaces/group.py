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
group interfaces for plone, based off existing group usage pre pas. 

$Id: group.py,v 1.6 2005/02/19 20:03:49 k_vertigo Exp $
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

    def updateGroup(id, **kw):
        """
        Edit the given group. plugin specific 
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


