##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
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
$Id$
"""
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_users as ManageUsers
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem

from Products.CMFPlone import ToolNames
from Products.CMFPlone.GroupsTool import GroupsTool as PloneGroupsTool
from Products.CMFCore.utils import getToolByName, UniqueObject

from Products.PlonePAS.interfaces import group as igroup
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.utils import classImplements, implementedBy

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

    ##
    # basic group mgmt
    ##

    def addGroup(self, id, roles = [], groups = [], properties=None, *args, **kw):
        group = None
        success = 0
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            success = manager.addGroup(id, title=kw.get('title', id),
                                       description=kw.get('title', None))
            if success:
                self.setRolesForGroup(id, roles)
                for g in groups:
                    manager.addPrincipalToGroup(g.getId(), id)
                break

        if success:
            group = self.getGroupById(id)
            group.setGroupProperties(properties or kw)
            self.createGrouparea(id)
        return success

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
    def removeGroup(self, group_id, keep_workspaces=0):
        """Remove a single group, including group workspace, unless keep_workspaces==true."""
        retval = False
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'

        for mid, manager in managers:
            if manager.removeGroup(group_id):
                retval = True

        gwf = self.getGroupWorkspacesFolder()
        if retval and gwf and not keep_workspaces:
            workspace_id = self.getGroupareaFolder(group_id).getId()
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
            self.removeGroup(id, keep_workspaces)

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
    
    def searchForGroups(self, REQUEST={}, **kw):
        """Search for groups by keyword.
        The following properties can be searched:
        - name
        #- email
        #- title

        Only id/title search is implemented for groups. Is the rest of
        this junk used anywhere?

        This is an 'AND' request.

        When it takes 'name' as keyword (or in REQUEST) and searches on
        Full name and id.

        Simple name searches are "fast".
        """
        acl_users = self.acl_users
        groups_tool = self.portal_groups
        if REQUEST:
            dict = REQUEST
        else:
            dict = kw

        name = dict.get('name', None)
        #email = dict.get('email', None)
        #roles = dict.get('roles', None)
        #title = dict.get('title', None)
        title_or_name = dict.get('title_or_name', None)
        if name:
            name = name.strip().lower()
        if not name:
            name = None
        if title_or_name: name = title_or_name
        #if email:
        #    email = email.strip().lower()
        #if not email:
        #    email = None
        #if title:
        #    title = title.strip().lower()
        #if not title:
        #    title = None

        md_groups = []
        uf_groups = []

        if name:
            # This will allow us to retrieve groups by their id or title
            uf_groups = acl_users.searchGroups(name=name)

            # PAS allows search to return dupes. We must winnow...
            uf_groups_new = []
            for group in uf_groups:
                if group not in uf_groups_new:
                    uf_groups_new.append(group)
            uf_groups = uf_groups_new

        groups = []
        if md_groups or uf_groups:
            getGroupById = self.getGroupById

            for groupid in md_groups:
                groups.append(getGroupById(groupid))
            for group in uf_groups:
                groupid = group['groupid']
                if groupid in md_groups:
                    continue             # Kill dupes
                groups.append(getGroupById(groupid))

            #if not email and \
            #       not roles and \
            #       not last_login_time:
            #    return groups

        return groups


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

classImplements(GroupsTool,
                *tuple(implementedBy(PloneGroupsTool)) +
                (igroup.IGroupTool,))

InitializeClass(GroupsTool)
