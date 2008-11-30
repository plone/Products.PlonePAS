import logging
from sets import Set

from zope.deprecation import deprecate
from zope.interface import implements

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from AccessControl.User import nobody
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from ZODB.POSException import ConflictError

from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import _checkPermission

from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.PluggableAuthService import \
                                    _SWALLOWABLE_PLUGIN_EXCEPTIONS

from Products.PlonePAS.interfaces import group as igroup
from Products.PlonePAS.permissions import AddGroups
from Products.PlonePAS.permissions import ManageGroups
from Products.PlonePAS.permissions import DeleteGroups
from Products.PlonePAS.permissions import ViewGroups
from Products.PlonePAS.permissions import SetGroupOwnership


logger = logging.getLogger('PluggableAuthService')

class NotSupported(Exception): pass

class GroupsTool(UniqueObject, SimpleItem):
    """ This tool accesses group data through a acl_users object.

    It can be replaced with something that groups member data in a
    different way.
    """

    implements(igroup.IGroupTool)

    id = 'portal_groups'
    meta_type = 'PlonePAS Groups Tool'
    security = ClassSecurityInfo()
    toolicon = 'tool.gif'

    # No group workspaces by default
    groupworkspaces_id = "groups"
    groupworkspaces_title = "Groups"
    groupWorkspacesCreationFlag = 0
    groupWorkspaceType = "Folder"
    groupWorkspaceContainerType = "Folder"

    ##
    # basic group mgmt
    ##

    security.declareProtected(AddGroups, 'addGroup')
    @postonly
    def addGroup(self, id, roles = [], groups = [], properties=None, 
                 REQUEST=None, *args, **kw):
        """Create a group, and a group workspace if the toggle is on, with the supplied id, roles, and domains.

        Underlying user folder must support adding users via the usual Zope API.
        Passwords for groups ARE irrelevant in GRUF."""
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

    security.declareProtected(ManageGroups, 'editGroup')
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
                groupmanagers = self.acl_users.plugins.listPlugins(igroup.IGroupManagement)
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                logger.exception('Plugin listing error')
                groupmanagers = ()

            for group in groups:
                for gm_id, gm in groupmanagers:
                    try:
                        if gm.addPrincipalToGroup(id, group):
                            break
                    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                        logger.exception('AuthenticationPlugin %s error' % gm_id)

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

    security.declareProtected(ViewGroups, 'getGroupById')
    def getGroupById(self, group_id):
        group = self.acl_users.getGroup(group_id)
        if group is not None:
            group = self.wrapGroup(group)
        return group

    security.declareProtected(ManageGroups, 'searchGroups')
    @deprecate("portal_groups.searchGroups is deprecated and will "
               "be removed in Plone 3.5. Use PAS searchGroups instead")
    def searchGroups(self, *args, **kw):
        return self.acl_users.searchGroups(*args, **kw)

    @deprecate("portal_groups.searchForGroups is deprecated and will "
               "be removed in Plone 3.5. Use PAS searchGroups instead")
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
        title_or_name = dict.get('title_or_name', None)
        if name:
            name = name.strip().lower()
        if not name:
            name = None
        if title_or_name: name = title_or_name

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

        return groups

    security.declareProtected(ViewGroups, 'listGroups')
    @deprecate("portal_groups.listGroups is deprecated and will "
               "be removed in Plone 3.5. Use PAS searchGroups instead")
    def listGroups(self):
        # potentially not all groups may be found by this interface
        # if the underlying group source doesn't support introspection
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroups())
        return [self.wrapGroup(elt) for elt in groups]

    security.declareProtected(ViewGroups, 'getGroupIds')
    @deprecate("portal_groups.listGroups is deprecated and will "
               "be removed in Plone 3.5. Use PAS searchGroups instead")
    def getGroupIds(self):
        groups = []
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            groups.extend(introspector.getGroupIds())
        return groups

    listGroupIds = getGroupIds

    security.declareProtected(ViewGroups, 'getGroupMembers')
    @deprecate("portal_groups.getGroupMembers is deprecated and will "
               "be removed in Plone 3.5. Use PAS to get a group and check "
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
               "be removed in Plone 3.5. Use PAS to get a principal and check "
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

    ##
    # BBB
    ##

    security.declarePublic('getGroupInfo')
    def getGroupInfo(self, groupId):
        """
        Return default group info of any group
        """
        group = self.getGroupById(groupId)

        if group is None:
            return None

        groupinfo = { 'title'    : group.getProperty('title'),
                      'description' : group.getProperty('description'),
                    }

        return groupinfo

    security.declareProtected(ViewGroups, 'getGroupsByUserId')
    def getGroupsByUserId(self, userid):
        """Return a list of the groups the user corresponding to 'userid' belongs to."""
        #log("getGroupsByUserId(%s)" % userid)
        user = self.acl_users.getUser(userid)
        #log("user '%s' is in groups %s" % (userid, user.getGroups()))
        if user:
            groups = user.getGroups() or []
        else:
            groups = []
        return [self.getGroupById(elt) for elt in groups]

    security.declareProtected(ViewGroups, 'listGroupNames')
    def listGroupNames(self):
        """Return a list of the available groups' ids as entered (without group prefixes)."""
        return self.acl_users.getGroupNames()

    security.declarePublic("isGroup")
    def isGroup(self, u):
        """Test if a user/group object is a group or not.
        You must pass an object you get earlier with wrapUser() or wrapGroup()
        """
        base = aq_base(u)
        if hasattr(base, "isGroup") and base.isGroup():
            return 1
        return 0

    security.declareProtected(SetGroupOwnership, 'setGroupOwnership')
    @postonly
    def setGroupOwnership(self, group, object, REQUEST=None):
        """Make the object 'object' owned by group 'group' (a portal_groupdata-ish object).

        For GRUF this is easy. Others may have to re-implement."""
        user = group.getGroup()
        if user is None:
            raise ValueError, "Invalid group: '%s'." % (group, )
        object.changeOwnership(user)
        object.manage_setLocalRoles(user.getId(), ['Owner'])

    security.declareProtected(ManagePortal, 'setGroupWorkspacesFolder')
    def setGroupWorkspacesFolder(self, id="", title=""):
        """ Set the location of the Group Workspaces folder by id.

        The Group Workspaces Folder contains all the group workspaces, just like the
        Members folder contains all the member folders.

         If anyone really cares, we can probably make the id work as a path as well,
         but for the moment it's only an id for a folder in the portal root, just like the
         corresponding MembershipTool functionality. """
        self.groupworkspaces_id = id.strip()
        self.groupworkspaces_title = title

    security.declareProtected(ManagePortal, 'getGroupWorkspacesFolderId')
    def getGroupWorkspacesFolderId(self):
        """ Get the Group Workspaces folder object's id.

        The Group Workspaces Folder contains all the group workspaces, just like the
        Members folder contains all the member folders. """
        return self.groupworkspaces_id

    security.declareProtected(ManagePortal, 'getGroupWorkspacesFolderTitle')
    def getGroupWorkspacesFolderTitle(self):
        """ Get the Group Workspaces folder object's title.
        """
        return self.groupworkspaces_title

    security.declarePublic('getGroupWorkspacesFolder')
    def getGroupWorkspacesFolder(self):
        """ Get the Group Workspaces folder object.

        The Group Workspaces Folder contains all the group workspaces, just like the
        Members folder contains all the member folders. """
        parent = self.aq_inner.aq_parent
        folder = getattr(parent, self.getGroupWorkspacesFolderId(), None)
        return folder

    security.declareProtected(ManagePortal, 'toggleGroupWorkspacesCreation')
    def toggleGroupWorkspacesCreation(self, REQUEST=None):
        """ Toggles the flag for creation of a GroupWorkspaces folder upon creation of the group. """
        if not hasattr(self, 'groupWorkspacesCreationFlag'):
            self.groupWorkspacesCreationFlag = 0

        self.groupWorkspacesCreationFlag = not self.groupWorkspacesCreationFlag

        m = self.groupWorkspacesCreationFlag and 'turned on' or 'turned off'

    security.declareProtected(ManagePortal, 'getGroupWorkspacesCreationFlag')
    def getGroupWorkspacesCreationFlag(self):
        """Return the (boolean) flag indicating whether the Groups Tool will create a group workspace
        upon the creation of the group (if one doesn't exist already). """
        return self.groupWorkspacesCreationFlag

    security.declareProtected(AddGroups, 'createGrouparea')
    def createGrouparea(self, id):
        """Create a space in the portal for the given group, much like member home
        folders."""
        parent = self.aq_inner.aq_parent
        workspaces = self.getGroupWorkspacesFolder()
        pt = getToolByName( self, 'portal_types' )

        if id and self.getGroupWorkspacesCreationFlag():
            if workspaces is None:
                # add GroupWorkspaces folder
                pt.constructContent(
                    type_name = self.getGroupWorkspaceContainerType(),
                    container = parent,
                    id = self.getGroupWorkspacesFolderId(),
                    )
                workspaces = self.getGroupWorkspacesFolder()
                workspaces.setTitle(self.getGroupWorkspacesFolderTitle())
                workspaces.setDescription("Container for " + self.getGroupWorkspacesFolderId())
                # how about ownership?

                # this stuff like MembershipTool...
                workspaces._setProperty('right_slots', (), 'lines')
                
            if workspaces is not None and not hasattr(workspaces.aq_base, id):
                # add workspace to GroupWorkspaces folder
                pt.constructContent(
                    type_name = self.getGroupWorkspaceType(),
                    container = workspaces,
                    id = id,
                    )
                space = self.getGroupareaFolder(id)
                space.setTitle("%s workspace" % id)
                space.setDescription("Container for objects shared by this group")

                if hasattr(space, 'setInitialGroup'):
                    # GroupSpaces can have their own policies regarding the group
                    # that they are created for.
                    user = self.getGroupById(id).getGroup()
                    if user is not None:
                        space.setInitialGroup(user)
                else:
                    space.manage_delLocalRoles(space.users_with_local_role('Owner'))
                    self.setGroupOwnership(self.getGroupById(id), space)

                # Hook to allow doing other things after grouparea creation.
                notify_script = getattr(workspaces, 'notifyGroupAreaCreated', None)
                if notify_script is not None:
                    notify_script()

                # Re-indexation
                portal_catalog = getToolByName( self, 'portal_catalog' )
                portal_catalog.reindexObject(space)

    security.declareProtected(ManagePortal, 'getGroupWorkspaceType')
    def getGroupWorkspaceType(self):
        """Return the Type (as in TypesTool) to make the GroupWorkspace."""
        return self.groupWorkspaceType

    security.declareProtected(ManagePortal, 'setGroupWorkspaceType')
    def setGroupWorkspaceType(self, type):
        """Set the Type (as in TypesTool) to make the GroupWorkspace."""
        self.groupWorkspaceType = type

    security.declareProtected(ManagePortal, 'getGroupWorkspaceContainerType')
    def getGroupWorkspaceContainerType(self):
        """Return the Type (as in TypesTool) to make the GroupWorkspace."""
        return self.groupWorkspaceContainerType

    security.declareProtected(ManagePortal, 'setGroupWorkspaceContainerType')
    def setGroupWorkspaceContainerType(self, type):
        """Set the Type (as in TypesTool) to make the GroupWorkspace."""
        self.groupWorkspaceContainerType = type

    security.declarePublic('getGroupareaFolder')
    def getGroupareaFolder(self, id=None, verifyPermission=0):
        """Returns the object of the group's work area."""
        workspaces = self.getGroupWorkspacesFolder()
        if workspaces:
            try:
                folder = workspaces[id]
                if verifyPermission and not _checkPermission('View', folder):
                    # Don't return the folder if the user can't get to it.
                    return None
                return folder
            except KeyError: pass
        return None

    security.declarePublic('getGroupareaURL')
    def getGroupareaURL(self, id=None, verifyPermission=0):
        """Returns the full URL to the group's work area."""
        ga = self.getGroupareaFolder(id, verifyPermission)
        if ga is not None:
            return ga.absolute_url()
        else:
            return None

    security.declarePrivate('wrapGroup')
    def wrapGroup(self, g, wrap_anon=0):
        ''' Sets up the correct acquisition wrappers for a group
        object and provides an opportunity for a portal_memberdata
        tool to retrieve and store member data independently of
        the user object.
        '''
        b = getattr(g, 'aq_base', None)
        if b is None:
            # u isn't wrapped at all.  Wrap it in self.acl_users.
            b = g
            g = g.__of__(self.acl_users)
        if (b is nobody and not wrap_anon) or hasattr(b, 'getMemberId'):
            # This user is either not recognized by acl_users or it is
            # already registered with something that implements the
            # member data tool at least partially.
            return g

        parent = self.aq_inner.aq_parent
        base = getattr(parent, 'aq_base', None)
        if hasattr(base, 'portal_groupdata'):
            # Get portal_groupdata to do the wrapping.
            gd = getToolByName(parent, 'portal_groupdata')
            try:
                #log("wrapping group %s" % g)
                portal_group = gd.wrapGroup(g)
                return portal_group
            except ConflictError:
                raise
            except:
                logger.exception('Error during wrapGroup')
        # Failed.
        return g


InitializeClass(GroupsTool)
registerToolInterface('portal_groups', igroup.IGroupTool)
