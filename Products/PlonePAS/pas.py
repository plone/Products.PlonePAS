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
pas alterations and monkies
$Id: pas.py,v 1.31 2005/07/06 21:44:39 jccooper Exp $
"""
import sys
from sets import Set

from Acquisition import aq_inner, aq_parent
from AccessControl.PermissionRole import _what_not_even_god_should_do
from AccessControl.Permissions import manage_users as ManageUsers

from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.PluggableAuthService import \
     PluggableAuthService, _SWALLOWABLE_PLUGIN_EXCEPTIONS, LOG, BLATHER
from Products.PluggableAuthService.PluggableAuthService import security
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin

from Products.PlonePAS.interfaces.plugins import IUserManagement, ILocalRolesPlugin
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PlonePAS.interfaces.plugins import IUserIntrospection

#################################
# pas folder monkies - standard zope user folder api

def _doDelUsers(self, ids):
    """
    Given a list of user ids, hand off to a deleter plugin if available;
    has no return value, like the original
    """

    plugins = self._getOb('plugins')
    userdeleters = plugins.listPlugins(IUserManagement)

    if not userdeleters:
        raise NotImplementedError("There is no plugin that can "
                                   " delete users.")

    for userdeleter_id, userdeleter in userdeleters:
        for id in ids:
            userdeleter.doDeleteUser(id)

PluggableAuthService._doDelUsers = _doDelUsers

security.declareProtected(ManageUsers, 'userFolderDelUsers')
PluggableAuthService.userFolderDelUsers = PluggableAuthService._doDelUsers


def _doChangeUser(self, principal_id, password, roles, domains=(), **kw):
    """
    Given a principal id, change its password, roles, domains, iff
    respective plugins for such exist.

    XXX domains are currently ignored.
    """
    self.userSetPassword(principal_id, password)

    plugins = self._getOb('plugins')
    rmanagers = plugins.listPlugins(IRoleAssignerPlugin)

    if not (rmanagers):
        raise NotImplementedError("There is no plugin that can modify roles")

    for rid, rmanager in rmanagers:
        rmanager.assignRolesToPrincipal(roles, principal_id)

    return True

PluggableAuthService._doChangeUser = _doChangeUser

security.declareProtected(ManageUsers, 'userFolderEditUser')
PluggableAuthService.userFolderEditUser = PluggableAuthService._doChangeUser


# ttw alias
# XXX need to security restrict these methods, no base class sec decl
#PluggableAuthService.userFolderAddUser__roles__ = ()
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser


# for prefs_group_manage compatibility. really should be using tool.
def _doDelGroups(self, names):
    gtool = getToolByName(self, 'portal_groups')
    for group_id in names:
        gtool.removeGroup(group_id)

PluggableAuthService._doDelGroups = _doDelGroups

security.declareProtected(ManageUsers, 'userFolderDelGroups')
PluggableAuthService.userFolderDelGroups = PluggableAuthService._doDelGroups



def _doChangeGroup(self, principal_id, roles, groups=None, **kw):
    """
    Given a group's id, change its roles, domains, iff respective
    plugins for such exist.

    XXX domains are currently ignored.
    XXX groups also ignored

    See also _doChangeUser
    """

    plugins = self._getOb('plugins')
    rmanagers = plugins.listPlugins(IRoleAssignerPlugin)


    if not (rmanagers):
        raise NotImplementedError("There is no plugin that can modify users")

    for rid, rmanager in rmanagers:
        rmanager.assignRolesToPrincipal(roles, principal_id)

    return True

PluggableAuthService._doChangeGroup = _doChangeGroup

security.declareProtected(ManageUsers, 'userFolderEditGroup')
PluggableAuthService.userFolderEditGroup = PluggableAuthService._doChangeGroup

security.declareProtected(ManageUsers, 'getGroup')
def getGroup(self, group_id):
    """Like getGroupById in groups tool, but doesn't wrap.
    """
    group = None
    introspectors = self.plugins.listPlugins(IGroupIntrospection)

    if not introspectors:
        raise NotSupported, 'No plugins allow for group management'
    for iid, introspector in introspectors:
        group = introspector.getGroupById(group_id)
        if group is None:
            break
    return group
PluggableAuthService.getGroup = getGroup


security.declarePublic("getLocalRolesForDisplay")
def getLocalRolesForDisplay(self, object):
    """This is used for plone's local roles display

    This method returns a tuple (massagedUsername, roles, userType,
    actualUserName).  This method is protected by the 'access content
    information' permission. We may change that if it's too
    permissive...

    A GRUF method originally.
    """
    result = []
    # we don't have a PAS-side way to get this
    local_roles = object.get_local_roles()
    for one_user in local_roles:
        username = one_user[0]
        roles = one_user[1]
        userType = 'user'
        if self.getGroup(username):
            userType = 'group'
        result.append((username, roles, userType, username))
    return tuple(result)
PluggableAuthService.getLocalRolesForDisplay = getLocalRolesForDisplay


def getUsers(self):
    """
    Return a list of all users from plugins that implement the user
    introspection interface.

    Could potentially be very long.
    """
    # We should have a method that's cheap about returning number of users.
    retval = []
    plugins = self._getOb('plugins')
    introspectors = self.plugins.listPlugins(IUserIntrospection)

    for iid, introspector in introspectors:
        retval += introspector.getUsers()

    return retval
PluggableAuthService.getUsers = getUsers
PluggableAuthService.getPureUsers = getUsers   # this'll make listMembers work


def canListAllUsers(self):
    plugins = self._getOb('plugins')

    # Do we have multiple user plugins?
    if len(plugins.listPlugins(IUserEnumerationPlugin)) != len(plugins.listPlugins(IUserIntrospection)):
        return False

    # Does our single user enumerator support the needed API?
    #for method in [#'countAllUsers',
    #               'getUsers',
    #               'getUserNames']:
    #    if not hasattr(pas, method):
    #        return False

    return True
PluggableAuthService.canListAllUsers = canListAllUsers


def canListAllGroups(self):
    plugins = self._getOb('plugins')

    # Do we have multiple user plugins?
    if len(plugins.listPlugins(IGroupEnumerationPlugin)) != len(plugins.listPlugins(IGroupIntrospection)):
        return False
    return True
PluggableAuthService.canListAllGroups = canListAllGroups


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
            modified = True
        except RuntimeError:
            pass

    if not modified:
        raise RuntimeError ("No user management plugins were able "
                            "to successfully modify the user")
    
PluggableAuthService.userSetPassword = userSetPassword


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




#################################
# non standard gruf --- junk method  XXX remove me

def _doDelUsers(self, names):
    """Delete one or more users. This should be implemented by
    subclasses to do the actual deleting of users.
    """
    for name in names:
        self._doDelUser(name)

PluggableAuthService._doDelUsers = _doDelUsers
