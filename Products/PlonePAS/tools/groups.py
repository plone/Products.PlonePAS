"""
$Id: groups.py,v 1.15 2005/05/26 01:32:48 dreamcatcher Exp $
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

class NotSupported(Exception): pass

class GroupsTool(PloneGroupsTool):
    """
    Gor the groupie in you
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

    security.declareProtected(ManageUsers, 'addGroup')
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

    security.declareProtected(ManageUsers, 'removeGroup')
    def removeGroup(self, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            if manager.removeGroup(group_id):
                return True
        return False

    security.declareProtected(ManageUsers, 'setRolesForGroup')
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

    security.declareProtected(ManageUsers, 'addPrincipalToGroup')
    def addPrincipalToGroup(self, principal_id, group_id):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            if manager.addPrincipalToGroup(principal_id, group_id):
                return True
        return False

    security.declareProtected(ManageUsers, 'removePrincipalFromGroup')
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

    security.declareProtected(ManageUsers, 'getGroupById')
    def getGroupById(self, group_id):
        group = self.acl_users.getGroup(group_id)
        if group is not None:
            group = self.wrapGroup(group)
        return group

    security.declareProtected(ManageUsers, 'searchGroups')
    def searchGroups(self, *args, **kw):
        # XXX document interface.. returns a list of dictionaries
        return self.acl_users.searchGroups(*args, **kw)

    security.declareProtected(ManageUsers, 'listGroups')
    def listGroups(self):
        # potentially not all groups may be found by this interface
        # if the underlying group source doesn't support introspection
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroups())
        return [self.wrapGroup(elt) for elt in groups]

    security.declareProtected(ManageUsers, 'getGroupIds')
    def getGroupIds(self):
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroupIds())
        return groups

    security.declareProtected(ManageUsers, 'getGroupMembers')
    def getGroupMembers(self, group_id):
        members = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            members = introspector.getGroupMembers(group_id)
            if members:
                break
        return members

    security.declareProtected(ManageUsers, 'getGroupsForPrincipal')
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
