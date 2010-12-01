import logging

from zope.interface import implements

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from AccessControl.User import nobody
from App.class_init import InitializeClass
from OFS.SimpleItem import SimpleItem
from ZODB.POSException import ConflictError

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject

from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.PluggableAuthService import \
                                    _SWALLOWABLE_PLUGIN_EXCEPTIONS

from Products.PlonePAS.interfaces import group as igroup
from Products.PlonePAS.permissions import AddGroups
from Products.PlonePAS.permissions import ManageGroups
from Products.PlonePAS.permissions import DeleteGroups
from Products.PlonePAS.permissions import ViewGroups
from Products.PlonePAS.permissions import SetGroupOwnership
from Products.PlonePAS.utils import getGroupsForPrincipal


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

    ##
    # basic group mgmt
    ##

    security.declareProtected(AddGroups, 'addGroup')
    @postonly
    def addGroup(self, id, roles = [], groups = [], properties=None,
                 REQUEST=None, *args, **kw):
        """Create a group, with the supplied id, roles, and domains.

        Underlying user folder must support adding users via the usual Zope API.
        """
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
                                       description=kw.get('description', ''))
            if success:
                self.setRolesForGroup(id, roles)
                for g in groups:
                    manager.addPrincipalToGroup(g, id)
                break

        if success:
            group = self.getGroupById(id)
            group.setGroupProperties(properties or kw)

        return success

    security.declareProtected(ManageGroups, 'editGroup')
    @postonly
    def editGroup(self, id, roles=None, groups=None, REQUEST=None, *args, **kw):
        """Edit the given group with the supplied roles.

        Passwords for groups seem to be irrelevant.
        PlonePAS doesn't deal with domains either.

        If group is not present, returns without exception.
        """
        g = self.getGroupById(id)
        if not g:
            raise KeyError, 'Trying to edit a non-existing group: %s' % id

        # Update title/description properties of original group
        gTools = self._getGroupTools()
        if not gTools:
            raise NotSupported, 'No plugins allow for both group management and introspection'

        for tid, tool in gTools:
            if id in tool.getGroupIds():
                tool.updateGroup(id, title=kw.get('title'),
                                     description=kw.get('description'))
                break

        if roles is not None:
            self.setRolesForGroup(id, roles)

        g.setGroupProperties(kw)
        if groups:
            # remove absent groups
            groupset = set(groups)
            p_groups = set(self.getGroupsForPrincipal(g))
            rmgroups = p_groups - groupset
            for gid in rmgroups:
                if gid != 'AuthenticatedUsers':
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
    def removeGroup(self, group_id, REQUEST=None):
        """Remove a single group.
        """
        retval = False
        managers = self._getGroupManagers()
        if not managers:
            raise NotSupported, 'No plugins allow for group management'

        for mid, manager in managers:
            if manager.removeGroup(group_id):
                retval = True

        return retval

    security.declareProtected(DeleteGroups, 'removeGroups')
    @postonly
    def removeGroups(self, ids, REQUEST=None):
        """Remove the group in the provided list (if possible).
        """
        for gid in ids:
            self.removeGroup(gid)

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
    def searchGroups(self, *args, **kw):
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
        if REQUEST:
            dict = REQUEST
        else:
            dict = kw

        name = dict.get('name', None)
        title_or_name = dict.get('title_or_name', None)
        if name:
            name = name.strip().lower()
        if name is not None:
            name = None
        if title_or_name is not None: name = title_or_name

        md_groups = []
        uf_groups = []

        if name is not None:
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
        members = set()
        introspectors = self._getGroupIntrospectors()
        for iid, introspector in introspectors:
            members.update(introspector.getGroupMembers(group_id))
        return list(members)

    security.declareProtected(ViewGroups, 'getGroupsForPrincipal')
    def getGroupsForPrincipal(self, principal):
        return getGroupsForPrincipal(principal, self._getPlugins())

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

    security.declarePrivate('_getGroupTools')
    def _getGroupTools(self):
        managers = self._getPlugins().listPlugins(
            igroup.IGroupManagement
            )
        return [(id, manager) for (id, manager) in managers if igroup.IGroupIntrospection.providedBy(manager)]

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
        """Make the object  'object' owned by group 'group' (a portal_groupdata-ish object).

        For GRUF this is easy. Others may have to re-implement."""
        user = group.getGroup()
        if user is None:
            raise ValueError, "Invalid group: '%s'." % (group, )
        object.changeOwnership(user)
        object.manage_setLocalRoles(user.getId(), ['Owner'])

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
