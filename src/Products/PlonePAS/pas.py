# -*- coding: utf-8 -*-
# pas alterations and monkies
from AccessControl import Unauthorized
from AccessControl import getSecurityManager
from AccessControl.PermissionRole import PermissionRole
from AccessControl.Permissions import change_permissions
from AccessControl.Permissions import manage_properties
from AccessControl.Permissions import manage_users as ManageUsers
from AccessControl.requestmethod import postonly
from OFS.Folder import Folder
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.patch import ORIG_NAME
from Products.PlonePAS.patch import wrap_method
from Products.PluggableAuthService.PluggableAuthService import \
    PluggableAuthService
from Products.PluggableAuthService.PluggableAuthService import \
    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.events import PrincipalDeleted
from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IRoleAssignerPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IUserEnumerationPlugin
from zope.event import notify
import logging

logger = logging.getLogger('PlonePAS')

registerToolInterface('acl_users', IPluggableAuthService)


#################################
# helper functions

def _userSetGroups(pas, user_id, groupnames):
    """method was used at GRUF level, but is used inside this monkies at several
    places too.

    We no longer provide it on PAS to clean up patches

    """
    plugins = pas.plugins
    gtool = getToolByName(pas, "portal_groups")

    member = pas.getUserById(user_id)
    groupnameset = set(groupnames)

    # remove absent groups
    groups = set(gtool.getGroupsForPrincipal(member))
    rmgroups = groups - groupnameset
    for gid in rmgroups:
        try:
            gtool.removePrincipalFromGroup(user_id, gid)
        except KeyError:
            # We could hit a group which does not allow user removal, such as
            # created by our AutoGroup plugin.
            pass

    # add groups
    try:
        groupmanagers = plugins.listPlugins(IGroupManagement)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info(
            'PluggableAuthService: Plugin listing error',
            exc_info=1
        )
        groupmanagers = ()

    for group in groupnames:
        for gm_id, gm in groupmanagers:
            try:
                if gm.addPrincipalToGroup(user_id, group):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                logger.info(
                    'PluggableAuthService: GroupManagement %s error',
                    gm_id,
                    exc_info=1
                )

#################################
# pas folder monkies - standard zope user folder api or GRUF


def _doAddUser(self, login, password, roles, domains, groups=None, **kw):
    """Masking of PAS._doAddUser to add groups param."""
    _old_doAddUser = getattr(self, getattr(_doAddUser, ORIG_NAME))
    retval = _old_doAddUser(login, password, roles, domains)
    if groups is not None:
        _userSetGroups(self, login, groups)
    return retval


def _doDelUsers(self, names, REQUEST=None):
    """
    Delete users given by a list of user ids.
    Has no return value, like the original (GRUF).
    """
    for name in names:
        self._doDelUser(name)


def _doDelUser(self, id):
    """
    Given a user id, hand off to a deleter plugin if available.
    """
    plugins = self._getOb('plugins')
    userdeleters = plugins.listPlugins(IUserManagement)

    if not userdeleters:
        raise NotImplementedError(
            "There is no plugin that can delete users."
        )

    for userdeleter_id, userdeleter in userdeleters:
        try:
            userdeleter.doDeleteUser(id)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            pass
        else:
            notify(PrincipalDeleted(id))


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
        _userSetGroups(self, principal_id, groups)

    return True


def userFolderAddUser(self, login, password, roles, domains,
                      groups=None, REQUEST=None, **kw):
    self._doAddUser(login, password, roles, domains, **kw)
    if groups is not None:
        _userSetGroups(self, login, groups)


def _doAddGroup(self, id, roles, groups=None, **kw):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.addGroup(id, roles, groups, **kw)


# for prefs_group_manage compatibility. really should be using tool.
def _doDelGroups(self, names, REQUEST=None):
    gtool = getToolByName(self, 'portal_groups')
    for group_id in names:
        gtool.removeGroup(group_id)


def _doChangeGroup(self, principal_id, roles, groups=None, REQUEST=None, **kw):
    """
    Given a group's id, change its roles, domains, if respective
    plugins for such exist. Domains are currently ignored.

    See also _doChangeUser
    """
    gtool = getToolByName(self, 'portal_groups')
    gtool.editGroup(principal_id, roles, groups, **kw)
    return True


def _updateGroup(self, principal_id, roles=None, groups=None, **kw):
    """
    Given a group's id, change its roles, groups, if respective
    plugins for such exist. Domains are ignored.

    This is not an alias to _doChangeGroup because its params are different
    (slightly).
    """
    return self._doChangeGroup(principal_id, roles, groups, **kw)


def getGroups(self):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.listGroups()


def getGroupNames(self):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.getGroupIds()


def getGroupIds(self):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.getGroupIds()


def getGroup(self, group_id):
    """Like getGroupById in groups tool, but doesn't wrap.
    """
    group = None
    introspectors = self.plugins.listPlugins(IGroupIntrospection)

    if not introspectors:
        raise ValueError('No plugins allow for group management')
    for iid, introspector in introspectors:
        group = introspector.getGroupById(group_id)
        if group is not None:
            break
    return group


def getGroupByName(self, name, default=None):
    ret = self.getGroup(name)
    if ret is None:
        return default
    return ret


def getGroupById(self, id, default=None):
    gtool = getToolByName(self, "portal_groups")
    ret = gtool.getGroupById(id)
    if ret is None:
        return default
    else:
        return ret


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
        raise Unauthorized(name="getLocalRolesForDisplay")

    return self._getLocalRolesForDisplay(object)


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


def canListAllUsers(self):
    plugins = self._getOb('plugins')
    # Do we have multiple user plugins?
    num_enumeration_plugins = plugins.listPlugins(IUserEnumerationPlugin)
    num_introspection_plugins = plugins.listPlugins(IUserEnumerationPlugin)
    return num_enumeration_plugins == num_introspection_plugins


def canListAllGroups(self):
    plugins = self._getOb('plugins')
    # Do we have multiple group plugins?
    num_enumeration_plugins = plugins.listPlugins(IGroupEnumerationPlugin)
    num_introspection_plugins = plugins.listPlugins(IGroupEnumerationPlugin)
    return num_enumeration_plugins == num_introspection_plugins


def userSetPassword(self, userid, password):
    """Emulate GRUF 3 call for password set, for use with PwRT."""
    # used by _doChangeUser
    plugins = self._getOb('plugins')
    managers = plugins.listPlugins(IUserManagement)

    if not managers:
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
        raise RuntimeError("No user management plugins were able "
                           "to successfully modify the user")


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


# for ZopeVersionControl, we need to check 'plugins' for more than
# existence, since it replaces objects (like 'plugins') with SimpleItems
# and calls _delOb, which tries to use special methods of 'plugins'
def _delOb(self, id):
    #
    #   Override ObjectManager's version to clean up any plugin
    #   registrations for the deleted object
    #
    # XXX imo this is a evil one
    #
    plugins = self._getOb('plugins', None)

    if getattr(plugins, 'removePluginById', None) is not None:
        plugins.removePluginById(id)

    Folder._delOb(self, id)


def addRole(self, role):
    plugins = self._getOb('plugins')
    roles = plugins.listPlugins(IRoleAssignerPlugin)

    for plugin_id, plugin in roles:
        try:
            plugin.addRole(role)
            break
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            pass


def getAllLocalRoles(self, context):
    # Perform security check on destination object
    if not getSecurityManager().checkPermission(change_permissions, context):
        raise Unauthorized(name="getAllLocalRoles")
    return self._getAllLocalRoles(context)


def _getAllLocalRoles(self, context):
    plugins = self._getOb('plugins')
    lrmanagers = plugins.listPlugins(ILocalRolesPlugin)

    roles = {}
    for lrid, lrmanager in lrmanagers:
        newroles = lrmanager.getAllLocalRolesInContext(context)
        for k, v in newroles.items():
            if k not in roles:
                roles[k] = set()
            roles[k].update(v)

    return roles


def authenticate(self, name, password, request):
    """See AccessControl.User.BasicUserFolder.authenticate

    Products.PluggableAuthService.PluggableAuthService does not provide this
    method, BasicUserFolder documents it as "Private UserFolder object
    interface". GRUF does provide the method, so not marked as private.

    should be deprecated in future!
    """

    plugins = self.plugins

    try:
        authenticators = plugins.listPlugins(IAuthenticationPlugin)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        authenticators = ()

    credentials = {'login': name,
                   'password': password}

    user_id = None

    for authenticator_id, auth in authenticators:
        try:
            uid_and_name = auth.authenticateCredentials(credentials)
            if uid_and_name is not None:
                user_id, name = uid_and_name
                break
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info(
                'PluggableAuthService: AuthenticationPlugin %s error',
                authenticator_id,
                exc_info=1
            )
            continue

    if not user_id:
        return

    return self._findUser(plugins, user_id, name, request)


def getUserIds(self):
    """method was used at GRUF and is here for bbb. Not good for many users!
    DEPRECATED
    """
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserIds())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info(
                'PluggableAuthService: UserIntrospection %s error',
                introspector_id,
                exc_info=1
            )

    return results


def getUserNames(self):
    """method was used at GRUF and is here for bbb. Not good for many users!
    DEPRECATED
    """
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserNames())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info(
                'PluggableAuthService: UserIntroSpection plugin %s error',
                introspector_id, exc_info=1)

    return results


def patch_pas():
    # sort alphabetically by patched/added method name
    wrap_method(
        PluggableAuthService,
        '_delOb',
        _delOb
    )
    wrap_method(
        PluggableAuthService,
        '_getAllLocalRoles',
        _getAllLocalRoles,
        add=True,
    )
    wrap_method(
        PluggableAuthService,
        '_doAddGroup',
        _doAddGroup,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        '_doAddUser',
        _doAddUser
    )
    wrap_method(
        PluggableAuthService,
        '_doChangeGroup',
        _doChangeGroup,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        '_doChangeUser',
        _doChangeUser,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        '_doDelGroups',
        _doDelGroups,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        '_doDelUser',
        _doDelUser,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        '_doDelUsers',
        _doDelUsers,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        '_getLocalRolesForDisplay',
        _getLocalRolesForDisplay,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        '_updateGroup',
        _updateGroup,
        add=True
    )
    wrap_method(
        PluggableAuthService,
        'addRole',
        addRole,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'authenticate',
        authenticate,
        add=True,
        roles=(),
    )
    wrap_method(
        PluggableAuthService,
        'canListAllGroups',
        canListAllGroups,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'canListAllUsers',
        canListAllUsers,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'credentialsChanged',
        credentialsChanged,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getAllLocalRoles',
        getAllLocalRoles,
        add=True,
    )
    wrap_method(
        PluggableAuthService,
        'getGroup',
        getGroup,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getGroupById',
        getGroupById,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getGroupByName',
        getGroupByName,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getGroupIds',
        getGroupIds,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getGroupNames',
        getGroupNames,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getGroups',
        getGroups,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getLocalRolesForDisplay',
        getLocalRolesForDisplay,
        add=True,
    )
    wrap_method(
        PluggableAuthService,
        'getUserIds',
        getUserIds,
        add=True,
        deprecated="Inefficient GRUF wrapper, use IUserIntrospection instead."
    )
    wrap_method(
        PluggableAuthService,
        'getUserNames',
        getUserNames,
        add=True,
        deprecated="Inefficient GRUF wrapper, use IUserIntrospection instead."
    )
    wrap_method(
        PluggableAuthService,
        'getUsers',
        getUsers,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'getPureUsers',
        getUsers,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'userFolderAddUser',
        postonly(userFolderAddUser),
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'userFolderDelUsers',
        postonly(_doDelUsers),
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'userFolderEditGroup',
        postonly(_doChangeGroup),
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'userFolderEditUser',
        postonly(_doChangeUser),
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'userFolderDelGroups',
        postonly(_doDelGroups),
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
    wrap_method(
        PluggableAuthService,
        'userSetGroups',
        _userSetGroups,
        add=True,
        deprecated="Method from GRUF was removed."
    )
    wrap_method(
        PluggableAuthService,
        'userSetPassword',
        userSetPassword,
        add=True,
        roles=PermissionRole(ManageUsers, ('Manager',))
    )
