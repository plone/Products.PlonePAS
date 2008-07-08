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
"""
import logging
from sets import Set

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Globals import InitializeClass

from zope.interface import implementedBy
from zope.deprecation import deprecate

from Products.CMFCore.utils import registerToolInterface
from Products.CMFPlone.GroupsTool import GroupsTool as PloneGroupsTool

from Products.PlonePAS.interfaces import group as igroup
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.PluggableAuthService import \
                                    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.GroupUserFolder.GroupsToolPermissions import ViewGroups, DeleteGroups, ManageGroups

log = logging.getLogger('PluggableAuthService').exception

class NotSupported(Exception): pass

class GroupsTool(PloneGroupsTool):
    """
    Replace the GRUF groups tool with PAS-specific methods.
    """

    id = 'portal_groups'
    meta_type = 'PlonePAS Groups Tool'
    security = ClassSecurityInfo()
    toolicon = 'tool.gif'

    ##
    # basic group mgmt
    ##

    security.declarePrivate('invalidateGroup')
    def invalidateGroup(self, id):
        view_name = '_findGroup-%s' % id
        self.acl_users.ZCacheable_invalidate(view_name=view_name)

    @postonly
    def addGroup(self, id, roles = [], groups = [], properties=None, 
                 REQUEST=None, *args, **kw):
        group = None
        success = 0
        managers = self._getGroupManagers()
        if roles is None:
            roles = []
        if groups is None:
            groups = []

        # Check to see if a user with the id already exists fail if it does
        results = self.acl_users.searchPrincipals(id=id, exact_match=True)
        if results:
            return 0

        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            success = manager.addGroup(id, title=kw.get('title', id),
                                       description=kw.get('title', None))
            if success:
                self.setRolesForGroup(id, roles)
                for g in groups:
                    manager.addPrincipalToGroup(g, id)
                break

        if success:
            group = self.getGroupById(id)
            group.setGroupProperties(properties or kw)
            self.createGrouparea(id)

        return success

    @postonly
    def editGroup(self, id, roles=None, groups=None, REQUEST=None, *args, **kw):
        """Edit the given group with the supplied roles.

        Passwords for groups seem to be irrelevant.
        PlonePAS doesn't deal with domains either.

        If user is not present, returns without exception.
        """
        g = self.getGroupById(id)
        if not g:
            raise KeyError, 'Trying to edit a non-existing group: %s' % id

        if roles is not None:
            self.setRolesForGroup(id, roles)
        g.setGroupProperties(kw)
        if groups:
            # remove absent groups
            groupset = Set(groups)
            p_groups = Set(self.getGroupsForPrincipal(g))
            rmgroups = p_groups - groupset
            for gid in rmgroups:
                self.removePrincipalFromGroup(g, gid)

            # add groups
            try:
                groupmanagers = self._getGroupManagers()
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                log('Plugin listing error')
                groupmanagers = ()

            for group in groups:
                for gm_id, gm in groupmanagers:
                    try:
                        if gm.addPrincipalToGroup(id, group):
                            break
                    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                        log('AuthenticationPlugin %s error' % gm_id)

    security.declareProtected(DeleteGroups, 'removeGroup')
    @postonly
    def removeGroup(self, group_id, keep_workspaces=0, REQUEST=None):
        """Remove a single group, including group workspace, unless
        keep_workspaces==true.
        """
        retval = False
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'

        for mid, manager in managers:
            if manager.removeGroup(group_id):
                retval = True

        gwf = self.getGroupWorkspacesFolder()
        if retval and gwf and not keep_workspaces:
            grouparea = self.getGroupareaFolder(group_id)
            if grouparea is not None:
                workspace_id = grouparea.getId()
                if hasattr(aq_base(gwf), workspace_id):
                    gwf._delObject(workspace_id)

        self.invalidateGroup(group_id)
        return retval

    security.declareProtected(DeleteGroups, 'removeGroups')
    @postonly
    def removeGroups(self, ids, keep_workspaces=0, REQUEST=None):
        """Remove the group in the provided list (if possible).

        Will by default remove this group's GroupWorkspace if it exists. You may
        turn this off by specifying keep_workspaces=true.
        """
        for id in ids:
            self.removeGroup(id, keep_workspaces)

    security.declareProtected(ManageGroups, 'setRolesForGroup')
    @postonly
    def setRolesForGroup(self, group_id, roles=(), REQUEST=None):
        rmanagers = self._getPlugins().listPlugins(IRoleAssignerPlugin)
        if not (rmanagers):
            raise NotImplementedError, ('There is no plugin that can '
                                        'assign roles to groups')
        for rid, rmanager in rmanagers:
            rmanager.assignRolesToPrincipal(roles, group_id)

        self.invalidateGroup(group_id)
    ##
    # basic principal mgmt
    ##

    security.declareProtected(ManageGroups, 'addPrincipalToGroup')
    @postonly
    def addPrincipalToGroup(self, principal_id, group_id, REQUEST=None):
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'
        for mid, manager in managers:
            if manager.addPrincipalToGroup(principal_id, group_id):
                return True
        return False

    security.declareProtected(ManageGroups, 'removePrincipalFromGroup')
    @postonly
    def removePrincipalFromGroup(self, principal_id, group_id, REQUEST=None):
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
    @deprecate("portal_groups.searchForGroups is deprecated and will "
               "be removed in Plone 4.0. Use PAS searchGroups instead")
    def searchGroups(self, *args, **kw):
        # XXX document interface.. returns a list of dictionaries
        return self.acl_users.searchGroups(*args, **kw)

    @deprecate("portal_groups.searchForGroups is deprecated and will "
               "be removed in Plone 4.0. Use PAS searchGroups instead")
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
            # This will allow us to retrieve groups by their id only
            uf_groups = acl_users.searchGroups(id=name)

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

    @deprecate("portal_groups.listGroups is deprecated and will "
               "be removed in Plone 4.0. Use PAS searchGroups instead")
    def listGroups(self):
        # potentially not all groups may be found by this interface
        # if the underlying group source doesn't support introspection
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroups())
        return [self.wrapGroup(elt) for elt in groups]

    security.declareProtected(ViewGroups, 'getGroupIds')
    @deprecate("portal_groups.getGroupIds is deprecated and will "
               "be removed in Plone 4.0. Use PAS searchGroups instead")
    def getGroupIds(self):
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroupIds())
        return groups

    listGroupIds = getGroupIds

    security.declareProtected(ViewGroups, 'getGroupMembers')
    @deprecate("portal_groups.getGroupMembers is deprecated and will "
               "be removed in Plone 4.0. Use PAS to get a group and check "
               "its members instead.")
    def getGroupMembers(self, group_id):
        members = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            members = introspector.getGroupMembers(group_id)
            if members:
                break
        return members


    security.declareProtected(ViewGroups, 'getGroupsForPrincipal')
    @deprecate("portal_groups.getGroupsForPrincipal is deprecated and will "
               "be removed in Plone 4.0. Use PAS to get a principal and check "
               "its group list instead.")
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
        return self._getPlugins().listPlugins(
            igroup.IGroupManagement
            )

    security.declarePrivate('_getGroupIntrospectors')
    def _getGroupIntrospectors(self):
        return self._getPlugins().listPlugins(
            igroup.IGroupIntrospection
            )

    security.declarePrivate('_getGroupSpaceManagers')
    def _getGroupSpaceManagers(self):
        return self._getPlugins().listPlugins(
            igroup.IGroupSpaceManagers
            )

classImplements(GroupsTool,
                *tuple(implementedBy(PloneGroupsTool)) +
                (igroup.IGroupTool,))

InitializeClass(GroupsTool)
registerToolInterface('portal_groups', igroup.IGroupTool)
