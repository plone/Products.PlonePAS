"""
$Id: groups.py,v 1.3 2005/02/04 04:49:56 whit537 Exp $
"""
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.CMFPlone import ToolNames
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces import group as igroup

class NotSupported(Exception): pass

class GroupsTool(PloneBaseTool):
    """
    for the groupie in you
    """

    meta_type = ToolNames.GroupsTool
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/group.gif'

    __implements__ = ( PloneBaseTool.__implements__,
                       igroup.GroupTool )


    ##
    # basic group mgmt
    ##

    security.declareProtected(ManageGroups, 'addGroup')
    def addGroup(self, id, **kw):
        group = None
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported("no plugins allow for group management")
        for mid, manager in managers:
            group =  manager.addGroup( id, **kw )
            if group is not None:
                break
        return group

    security.declareProtected(ManageGroups, 'removeGroup')
    def removeGroup(self, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported("no plugins allow for group management")
        for mid, manager in managers:
            if manager.removeGroup( group_id ):
                return True
        return False

    security.declareProtected(ManageGroups, 'setRolesForGroup')
    def setRolesForGroup(self, group_id, roles=() ):
        # XXXX
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported("no plugins allow for group management")
        for mid, manager in managers:
            if manager.setRolesForGroup( group_id, roles ):
                return True



    ##
    # basic principal mgmt
    ##

    security.declareProtected(ManageGroups, 'addPrincipalToGroup')
    def addPrincipalToGroup(self, principal_id, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported("no plugins allow for group management")
        for mid, manager in managers:
            if manager.addPrincipalToGroup( principal_id, group_id):
                return True
        return False

    security.declareProtected(ManageGroups, 'removePrincipalFromGroup')
    def removePrincipalFromGroup( self, principal_id, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported("no plugins allow for group management")
        for mid, manager in managers:
            if manager.removePrincipalFromGroup( principal_id, group_id ):
                return True
        return False



    ##
    # group getters
    ##

    security.declareProtected(ManageGroups, 'getGroupById')
    def getGroupById( group_id ):
        group = None
        introspecters = self._getGroupIntrospecters()
        if not introspectors:
            raise NotSupported("no plugins allow for group management")
        for iid, introspecter in introspecters:
            group = introspecters.getGroupById( group_id )
            if group is None:
                break
        return group

    security.declareProtected(ManageGroups, 'searchGroups')
    def searchGroups(self, *args, **kw):
        # XXX document interface.. returns a list of dictionaries
        return self.acl_users.searchGroups( *args, **kw )

    security.declareProtected(ManageGroups, 'getGroups')
    def getGroups(self):
        # potentially not all groups may be found by this interface
        # if the underlying group source doesn't support introspection
        groups = []
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            groups.extend( introspecters.getGroups() )
        return groups

    security.declareProtected(ManageGroups, 'getGroupIds')
    def getGroupIds(self):
        groups = []
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            groups.extend( introspecters.getGroupIds() )
        return groups

    security.declareProtected(ManageGroups, 'getGroupMembers')
    def getGroupMembers(self, group_id):
        members = []
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            members = introspecters.getGroupMembers( group_id )
            if members:
                break
        return members

    security.declareProtected(ManageGroups, 'getGroupsForPrincipal')
    def getGroupsForPrincipal( principal_id, request=None ):
        return self.acl_users._getGroupsForPrincipal( principal_id, request )



    ##
    # plugin getters
    ##

    security.declarePrivate('_getPlugins')
    def _getPlugins(self):
        return self.acl_users.plugins

    security.declarePrivate('_getGroupManagers')
    def _getGroupManagers(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupManagement
            )

    security.declarePrivate('_getRoleManagers')
    def _getRoleManagers(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IRoleManager
            )

    security.declarePrivate('_getGroupIntrospecters')
    def _getGroupIntrospecters(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupIntrospection
            )

    security.declarePrivate('_getGroupSpaceManagers')
    def _getGroupSpaceManagers(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupSpaceManagers
            )


InitializeClass(GroupsTool)

