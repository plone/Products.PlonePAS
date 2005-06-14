"""
$Id: groups.py,v 1.18 2005/06/14 23:07:06 jccooper Exp $
"""
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_users as ManageUsers
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem

from Products.CMFPlone import ToolNames
from Products.CMFPlone.GroupsTool import GroupsTool as PloneGroupsTool
from Products.CMFCore.utils import getToolByName, UniqueObject

from Products.PlonePAS.interfaces import group as igroup
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin

from Products.GroupUserFolder.GroupsToolPermissions import ViewGroups, DeleteGroups, ManageGroups

class NotSupported(Exception): pass

class GroupsTool(PloneGroupsTool):
    """
    Replace the GRUF groups tool with PAS-specific methods.
    """

    id = 'portal_groups'
    meta_type = 'PlonePAS Groups Tool'
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/group.gif'

    __implements__ = (PloneGroupsTool.__implements__,
                      igroup.IGroupTool)

    ##
    # basic group mgmt
    ##

    def addGroup(self, id, roles = [], groups = [], properties=None, *args, **kw):
        group = None
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            manager.addGroup(id, title=kw.get('title', id),
                             description=kw.get('title', None))
            self.setRolesForGroup(id, roles)
            for g in groups:
                manager.addPrincipalToGroup(g.getId(), id)
        group = self.getGroupById(id)
        group.setGroupProperties(properties or kw)
        self.createGrouparea(id)

    def editGroup(self, id, password, roles, permissions):
        """Edit the given group with the supplied roles.

        Passwords for groups seem to be irrelevant.
        PlonePAS doesn't deal with domains either.

        If user is not present, returns without exception.
        """
        group = self.getGroupById(id)
        if not group: return None
        self.setRolesForGroup(id, roles)
        

    security.declareProtected(DeleteGroups, 'removeGroup')
    def removeGroup(self, group_id):
        """Remove a single group, including group workspace, unless keep_workspaces=true."""
        retval = False
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'

        for mid, manager in managers:
            if manager.removeGroup(group_id):
                retval = True

        gwf = self.getGroupWorkspacesFolder()
        if retval and gwf and not keep_workspaces:
            workspace_id = self.getGroupareaFolder().getId()
            if hasattr(aq_base(gwf), workspace_id):
                gwf._delObject(workspace_id)

        return retval

    security.declareProtected(DeleteGroups, 'removeGroups')
    def removeGroups(self, ids, keep_workspaces=0):
        """Remove the group in the provided list (if possible).

        Will by default remove this group's GroupWorkspace if it exists. You may
        turn this off by specifying keep_workspaces=true.
        """
        for id in ids:
            self.removeGroup(id)

    security.declareProtected(ManageGroups, 'setRolesForGroup')
    def setRolesForGroup(self, group_id, roles=()):
        rmanagers = self._getPlugins().listPlugins(IRoleAssignerPlugin)
        if not (rmanagers):
            raise NotImplementedError, ('There is no plugin that can '
                                        'assign roles to groups')
        for rid, rmanager in rmanagers:
            rmanager.assignRolesToPrincipal(roles, group_id)

    ##
    # basic principal mgmt
    ##

    security.declareProtected(ManageGroups, 'addPrincipalToGroup')
    def addPrincipalToGroup(self, principal_id, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            if manager.addPrincipalToGroup(principal_id, group_id):
                return True
        return False

    security.declareProtected(ManageGroups, 'removePrincipalFromGroup')
    def removePrincipalFromGroup(self, principal_id, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            if manager.removePrincipalFromGroup(principal_id, group_id):
                return True
        return False


    ##
    # group getters
    ##

    def getGroupById(self, group_id):
        group = self.acl_users.getGroup(group_id)
        if group is not None:
            group = self.wrapGroup(group)
        return group

    security.declareProtected(ManageGroups, 'searchGroups')
    def searchGroups(self, *args, **kw):
        # XXX document interface.. returns a list of dictionaries
        return self.acl_users.searchGroups(*args, **kw)
    
    def listGroups(self):
        # potentially not all groups may be found by this interface
        # if the underlying group source doesn't support introspection
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroups())
        return [self.wrapGroup(elt) for elt in groups]

    security.declareProtected(ViewGroups, 'getGroupIds')
    def getGroupIds(self):
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroupIds())
        return groups

    listGroupIds = getGroupIds

    security.declareProtected(ViewGroups, 'getGroupMembers')
    def getGroupMembers(self, group_id):
        members = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            members = introspector.getGroupMembers(group_id)
            if members:
                break
        return members

    security.declareProtected(ViewGroups, 'getGroupsForPrincipal')
    def getGroupsForPrincipal(self, principal):
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups = introspector.getGroupsForPrincipal(principal)
            if groups:
                break
        return groups

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

    security.declarePrivate('_getGroupIntrospectors')
    def _getGroupIntrospectors(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupIntrospection
            )

    security.declarePrivate('_getGroupSpaceManagers')
    def _getGroupSpaceManagers(self):
        return self.acl_users.plugins.listPlugins(
            igroup.IGroupSpaceManagers
            )


InitializeClass(GroupsTool)
