# pas alterations and monkies
from zope.event import notify

from Products.CMFCore.utils import getToolByName

from AccessControl import Unauthorized, getSecurityManager
from AccessControl.Permissions import manage_users as ManageUsers
from AccessControl.Permissions import manage_properties, change_permissions
from AccessControl.PermissionRole import PermissionRole

from Products.PluggableAuthService.PluggableAuthService import \
     PluggableAuthService, _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin
from Products.PluggableAuthService.events import PrincipalDeleted

from Products.PlonePAS.interfaces.plugins import IUserManagement, ILocalRolesPlugin
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from AccessControl.requestmethod import postonly

# Register the PAS acl_users as a utility
from Products.CMFCore.utils import registerToolInterface
from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService
registerToolInterface('acl_users', IPluggableAuthService)


#################################
# pas folder monkies - standard zope user folder api

_old_doAddUser = PluggableAuthService._doAddUser
def _doAddUser(self, login, password, roles, domains, groups=None, **kw ):
    """Masking of PAS._doAddUser to add groups param."""
    retval = _old_doAddUser(self, login, password, roles, domains)
    if groups is not None:
        self.userSetGroups(login, groups)
    return retval

PluggableAuthService._doAddUser = _doAddUser

def _doDelUsers(self, names, REQUEST=None):
    """
    Delete users given by a list of user ids.
    Has no return value, like the original (GRUF).
    """
    for name in names:
        self._doDelUser(name)

PluggableAuthService._doDelUsers = _doDelUsers


def _doDelUser(self, id):
    """
    Given a user id, hand off to a deleter plugin if available.
    """
    plugins = self._getOb('plugins')
    userdeleters = plugins.listPlugins(IUserManagement)

    if not userdeleters:
        raise NotImplementedError("There is no plugin that can "
                                   " delete users.")

    for userdeleter_id, userdeleter in userdeleters:
        try:
            userdeleter.doDeleteUser(id)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            pass
        else:
            notify(PrincipalDeleted(id))


PluggableAuthService._doDelUser = _doDelUser

PluggableAuthService.userFolderDelUsers = postonly(PluggableAuthService._doDelUsers)
PluggableAuthService.userFolderDelUsers__roles__ = PermissionRole(ManageUsers, ('Manager',))


def _doChangeUser(self, principal_id, password, roles, domains=(), groups=None,
                  REQUEST=None, **kw):
    """
    Given a principal id, change its password, roles, domains, if
    respective plugins for such exist.

    XXX domains are currently ignored.
    """
    # Might be called with 'None' as password from the Plone UI, in
    # prefs_users_overview when resetPassword is not set.
    if password is not None:
        self.userSetPassword(principal_id, password)

    plugins = self._getOb('plugins')
    rmanagers = plugins.listPlugins(IRoleAssignerPlugin)

    if not (rmanagers):
        raise NotImplementedError("There is no plugin that can modify roles")

    for rid, rmanager in rmanagers:
        rmanager.assignRolesToPrincipal(roles, principal_id)

    if groups is not None:
        self.userSetGroups(principal_id, groups)

    return True

PluggableAuthService._doChangeUser = _doChangeUser

PluggableAuthService.userFolderEditUser = postonly(PluggableAuthService._doChangeUser)
PluggableAuthService.userFolderEditUser__roles__ = PermissionRole(ManageUsers, ('Manager',))


def userFolderAddUser(self, login, password, roles, domains, groups=None, REQUEST=None, **kw ):
    self._doAddUser(login, password, roles, domains, **kw)
    if groups is not None:
        self.userSetGroups(login, groups)

PluggableAuthService.userFolderAddUser = postonly(userFolderAddUser)
PluggableAuthService.userFolderAddUser__roles__ = PermissionRole(ManageUsers, ('Manager',))


def _doAddGroup(self, id, roles, groups=None, **kw):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.addGroup(id, roles, groups, **kw)

PluggableAuthService._doAddGroup = _doAddGroup

# for prefs_group_manage compatibility. really should be using tool.
def _doDelGroups(self, names, REQUEST=None):
    gtool = getToolByName(self, 'portal_groups')
    for group_id in names:
        gtool.removeGroup(group_id)

PluggableAuthService._doDelGroups = _doDelGroups

PluggableAuthService.userFolderDelGroups = postonly(PluggableAuthService._doDelGroups)
PluggableAuthService.userFolderDelGroups__roles__ = PermissionRole(ManageUsers, ('Manager',))


def _doChangeGroup(self, principal_id, roles, groups=None, REQUEST=None, **kw):
    """
    Given a group's id, change its roles, domains, if respective
    plugins for such exist. Domains are currently ignored.

    See also _doChangeUser
    """
    gtool = getToolByName(self, 'portal_groups')
    gtool.editGroup(principal_id, roles, groups, **kw)
    return True
PluggableAuthService._doChangeGroup = _doChangeGroup

def _updateGroup(self, principal_id, roles=None, groups=None, **kw):
    """
    Given a group's id, change its roles, groups, if respective
    plugins for such exist. Domains are ignored.

    This is not an alias to _doChangeGroup because its params are different (slightly).
    """
    return self._doChangeGroup(principal_id, roles, groups, **kw)
PluggableAuthService._updateGroup = _updateGroup

PluggableAuthService.userFolderEditGroup = postonly(PluggableAuthService._doChangeGroup)
PluggableAuthService.userFolderEditGroup__roles__ = PermissionRole(ManageUsers, ('Manager',))


def getGroups(self):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.listGroups()
PluggableAuthService.getGroups = getGroups
PluggableAuthService.getGroups__roles__ = PermissionRole(ManageUsers, ('Manager',))

def getGroupNames(self):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.getGroupIds()
PluggableAuthService.getGroupNames = getGroupNames
PluggableAuthService.getGroupNames__roles__ = PermissionRole(ManageUsers, ('Manager',))

def getGroupIds(self):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.getGroupIds()
PluggableAuthService.getGroupIds = getGroupIds
PluggableAuthService.getGroupIds__roles__ = PermissionRole(ManageUsers, ('Manager',))

def getGroup(self, group_id):
    """Like getGroupById in groups tool, but doesn't wrap.
    """
    group = None
    introspectors = self.plugins.listPlugins(IGroupIntrospection)

    if not introspectors:
        raise ValueError, 'No plugins allow for group management'
    for iid, introspector in introspectors:
        group = introspector.getGroupById(group_id)
        if group is not None:
            break
    return group
PluggableAuthService.getGroup = getGroup
PluggableAuthService.getGroup__roles__ = PermissionRole(ManageUsers, ('Manager',))


def getGroupByName(self, name, default = None):
    ret = self.getGroup(name)
    if ret is None:
        return default
    return ret
PluggableAuthService.getGroupByName = getGroupByName
PluggableAuthService.getGroupByName__roles__ = PermissionRole(ManageUsers, ('Manager',))


def getGroupById(self, id, default = None):
    gtool = getToolByName(self, "portal_groups")
    ret = gtool.getGroupById(id)
    if ret is None:
        return default
    else:
        return ret
	    
PluggableAuthService.getGroupById = getGroupById
PluggableAuthService.getGroupById__roles__ = PermissionRole(ManageUsers, ('Manager',))


def getLocalRolesForDisplay(self, object):
    """This is used for plone's local roles display

    This method returns a tuple (massagedUsername, roles, userType,
    actualUserName).  This method is protected by the 'access content
    information' permission. We may change that if it's too
    permissive...

    A GRUF method originally.
    """
    # Perform security check on destination object
    if not getSecurityManager().checkPermission(manage_properties, object):
        raise Unauthorized(name = "getLocalRolesForDisplay")
    
    return self._getLocalRolesForDisplay(object)
PluggableAuthService.getLocalRolesForDisplay = getLocalRolesForDisplay
    
def _getLocalRolesForDisplay(self, object):
    result = []
    # we don't have a PAS-side way to get this
    local_roles = object.get_local_roles()
    for one_user in local_roles:
        username = userid = one_user[0]
        roles = one_user[1]
        userType = 'user'
        if self.getGroup(userid):
            userType = 'group'
        else:
            user = self.getUserById(userid) or self.getUser(username)
            if user:
                username = user.getUserName()
                userid = user.getId()
        result.append((username, roles, userType, userid))
    return tuple(result)
PluggableAuthService._getLocalRolesForDisplay = _getLocalRolesForDisplay


def getUsers(self):
    """
    Return a list of all users from plugins that implement the user
    introspection interface.

    Could potentially be very long.
    """
    # We should have a method that's cheap about returning number of users.
    retval = []
    try:
        introspectors = self.plugins.listPlugins(IUserIntrospection)
    except KeyError:
        return retval

    for iid, introspector in introspectors:
        retval += introspector.getUsers()

    return retval

PluggableAuthService.getUsers = getUsers
PluggableAuthService.getUsers__roles__ = PermissionRole(ManageUsers, ('Manager',))
PluggableAuthService.getPureUsers = getUsers   # this'll make listMembers work
PluggableAuthService.getPureUsers__roles__ = PermissionRole(ManageUsers, ('Manager',))


def canListAllUsers(self):
    plugins = self._getOb('plugins')

    # Do we have multiple user plugins?
    if len(plugins.listPlugins(IUserEnumerationPlugin)) != len(plugins.listPlugins(IUserIntrospection)):
        return False
    return True
PluggableAuthService.canListAllUsers = canListAllUsers
PluggableAuthService.canListAllUsers__roles__ = PermissionRole(ManageUsers, ('Manager',))


def canListAllGroups(self):
    plugins = self._getOb('plugins')

    # Do we have multiple user plugins?
    if len(plugins.listPlugins(IGroupEnumerationPlugin)) != len(plugins.listPlugins(IGroupIntrospection)):
        return False
    return True
PluggableAuthService.canListAllGroups = canListAllGroups
PluggableAuthService.canListAllGroups__roles__ = PermissionRole(ManageUsers, ('Manager',))


def userSetPassword(self, userid, password):
    """Emulate GRUF 3 call for password set, for use with PwRT."""
    # used by _doChangeUser
    plugins = self._getOb('plugins')
    managers = plugins.listPlugins(IUserManagement)

    if not (managers):
        raise NotImplementedError("There is no plugin that can modify users")

    modified = False
    for mid, manager in managers:
        try:
            manager.doChangeUser(userid, password)            
        except RuntimeError:
            # XXX: why silent ignore this Error?
            pass
        else:
            modified = True

    if not modified:
        raise RuntimeError ("No user management plugins were able "
                            "to successfully modify the user")
PluggableAuthService.userSetPassword = userSetPassword
PluggableAuthService.userSetPassword__roles__ = PermissionRole(ManageUsers, ('Manager',))


def credentialsChanged(self, user, name, new_password):
    """Notifies the authentication mechanism that this user has changed
    passwords.  This can be used to update the authentication cookie.
    Note that this call should *not* cause any change at all to user
    databases.

    For use by CMFCore.MembershipTool.credentialsChanged
    """
    request = self.REQUEST
    response = request.RESPONSE
    login = name

    self.updateCredentials(request, response, login, new_password)
PluggableAuthService.credentialsChanged = credentialsChanged
PluggableAuthService.credentialsChanged__roles__ = PermissionRole(ManageUsers, ('Manager',))


# for ZopeVersionControl, we need to check 'plugins' for more than
# existence, since it replaces objects (like 'plugins') with SimpleItems
# and calls _delOb, which tries to use special methods of 'plugins'
from OFS.Folder import Folder
def _delOb( self, id ):
    #
    #   Override ObjectManager's version to clean up any plugin
    #   registrations for the deleted object
    #
    # XXX imo this is a evil one
    #
    plugins = self._getOb( 'plugins', None )

    if getattr(plugins, 'removePluginById', None) is not None:
        plugins.removePluginById( id )

    Folder._delOb( self, id )
PluggableAuthService._delOb = _delOb

def addRole( self, role ):
    plugins = self._getOb('plugins')
    roles = plugins.listPlugins(IRoleAssignerPlugin)

    for plugin_id, plugin in roles:
        try:
            plugin.addRole( role )
            return
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            pass
PluggableAuthService.addRole = addRole
PluggableAuthService.addRole__roles__ = PermissionRole(ManageUsers, ('Manager',))


def getAllLocalRoles( self, context ):
    # Perform security check on destination object
    if not getSecurityManager().checkPermission(change_permissions, context):
        raise Unauthorized(name = "getAllLocalRoles")
    return self._getAllLocalRoles(context)
PluggableAuthService.getAllLocalRoles = getAllLocalRoles
    
def _getAllLocalRoles(self, context):
    plugins = self._getOb('plugins')
    lrmanagers = plugins.listPlugins(ILocalRolesPlugin)

    roles={}
    for lrid, lrmanager in lrmanagers:
        newroles=lrmanager.getAllLocalRolesInContext(context)
        for k,v in newroles.items():
            if k not in roles:
                roles[k]=set()
            roles[k].update(v)

    return roles
PluggableAuthService._getAllLocalRoles = _getAllLocalRoles