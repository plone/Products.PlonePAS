"""
$Id: groups.py,v 1.1 2005/02/03 00:09:49 k_vertigo Exp $
"""
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.CMFPlone import ToolNames
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces import group as igroup

class GroupsTool(PloneBaseTool):
    """
    for the groupie in you
    """
    
    meta_type = ToolNames.GroupsTool
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/group.gif'

    __implements__ = ( PloneBaseTool.__implements__,
                       igroup.GroupTool )

    def addGroup(self, id, **kw):
        group = None
        managers = self._getGroupManagers()
        for mid, manager in managers:
            group =  manager.addGroup( id, **kw )
            if group is not None:
                break
        return group

    def addPrincipalToGroup(self, principal_id, group_id):
        managers = self._getGroupManagers()
        for mid, manager in managers:
            if manager.addPrincipalToGroup( principal_id, group_id):
                return True
        return False

    def setRolesForGroup(self, group_id, roles=() ):
        # XXXX
        managers = self._getGroupManagers()
        for mid, manager in managers:
            if manager.setRolesForGroup( group_id, roles ):
                return True


    def removeGroup(self, group_id):
        managers = self._getGroupManagers()
        for mid, manager in managers:
            if manager.removeGroup( group_id ):
                return True
        return False

    def removePrincipalFromGroup( self, principal_id, group_id):
        managers = self._getGroupManagers()
        for mid, manager in managers:
            if manager.removePrincipalFromGroup( principal_id, group_id ):
                return True
        return False

    def getGroupById( group_id ):
        group = None        
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            group = introspecters.getGroupById( group_id )
            if group is None:
                break
        return group

    def searchGroups(self, *args, **kw):
        # XXX document interface.. returns a list of dictionaries
        return self.acl_users.searchGroups( *args, **kw )
    
    def getGroups(self):
        # potentially not all groups may be found by this interface
        # if the underlying group source doesn't support introspection
        groups = []
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            groups.extend( introspecters.getGroups() )
        return groups

    def getGroupIds(self):
        groups = []
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            groups.extend( introspecters.getGroupIds() )
        return groups        

    def getGroupMembers(self, group_id):
        members = []
        introspecters = self._getGroupIntrospecters()
        for iid, introspecter in introspecters:
            members = introspecters.getGroupMembers( group_id )
            if members:
                break
        return members

    def getGroupsForPrincipal( principal_id, request=None ):
        return self.acl_users._getGroupsForPrincipal( principal_id, request )
        
    def _getPlugins(self):
        return self.acl_users.plugins

    def _getGroupManagers(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupManagement
            )

    def _getGroupIntrospecters(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupIntrospection
            )

    def _getGroupSpaceManagers(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupSpaceManagers
            )
        

InitializeClass(GroupsTool)

