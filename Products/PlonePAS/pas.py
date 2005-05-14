"""
pas alterations and monkies
$Id: pas.py,v 1.22 2005/05/14 00:40:12 jccooper Exp $
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
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin, IAuthenticationPlugin

from Products.PlonePAS.interfaces.plugins import IUserManagement, ILocalRolesPlugin
from Products.PlonePAS.interfaces.group import IGroupIntrospection

#################################
# pas folder monkies - standard zope user folder api

def _doDelUsers(self, ids):
    """
    given a list of user ids, hand off to a deleter plugin if available;
    has no return value, like the original
    """

    plugins = self._getOb( 'plugins' )
    userdeleters = plugins.listPlugins( IUserManagement )

    if not userdeleters:
        raise NotImplementedError( "There is no plugin that can "
                                   " delete users." )

    for userdeleter_id, userdeleter in userdeleters:
        for id in ids:
            userdeleter.doDeleteUser(id)
        
PluggableAuthService._doDelUsers = _doDelUsers

security.declareProtected( ManageUsers, 'userFolderDelUsers' )
PluggableAuthService.userFolderDelUsers = PluggableAuthService._doDelUsers


def _doChangeUser(self, principal_id, password, roles, domains=(), **kw):
    """
    given a principal id, change its password, roles, domains, iff
    respective plugins for such exist.

    XXX domains are currently ignored.
    """

    plugins = self._getOb('plugins')
    managers = plugins.listPlugins( IUserManagement )
    rmanagers = plugins.listPlugins( IRoleAssignerPlugin )
    
    
    if not ( managers and rmanagers ):
        raise NotImplementedError( "There is no plugin that can modify users" )

    modified = False
    for mid, manager in managers:
        try:
            manager.doChangeUser( principal_id, password )
            modified = True
        except RuntimeError:
            pass

    if not modified:
        raise RuntimeError("no user management plugins were able to successfully modify the user")

#    sroles = Set() # keep track that we set all the requested roles
    for rid, rmanager in rmanagers:
        rmanager.assignRolesToPrincipal( roles, principal_id)   

#    # we can take care of this all in one call, now
#        for role in roles:
#            if rmanager.assignRolesToPrincipal( principal_id, role):
#                sroles.add( role )

#    roles_not_set = sroles.difference( Set( roles ) )
    
#    if not len( roles_not_set ) == 0:
#        raise RuntimeError("not all roles were set - %s"%roles_not_set)

    return True

PluggableAuthService._doChangeUser = _doChangeUser

security.declareProtected( ManageUsers, 'userFolderEditUser' )
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

security.declareProtected( ManageUsers, 'userFolderDelGroups' )
PluggableAuthService.userFolderDelGroups = PluggableAuthService._doDelGroups



def _doChangeGroup(self, principal_id, roles, groups=None, **kw):
    """
    given a group's id, change its roles, domains, iff respective plugins for such exist.

    XXX domains are currently ignored.
    XXX groups also ignored

    See also _doChangeUser
    """

    plugins = self._getOb('plugins')
    rmanagers = plugins.listPlugins( IRoleAssignerPlugin )
    
    
    if not ( rmanagers ):
        raise NotImplementedError( "There is no plugin that can modify users" )

    for rid, rmanager in rmanagers:
        rmanager.assignRolesToPrincipal( roles, principal_id)   

    return True

PluggableAuthService._doChangeGroup = _doChangeGroup

security.declareProtected( ManageUsers, 'userFolderEditGroup' )
PluggableAuthService.userFolderEditGroup = PluggableAuthService._doChangeGroup 



security.declareProtected(ManageUsers, 'getGroup')
def getGroup(self, group_id):
    """Like getGroupById in groups tool, but doesn't wrap."""
    group = None
    introspectors = self.plugins.listPlugins(IGroupIntrospection)

    if not introspectors:
        raise NotSupported("no plugins allow for group management")
    for iid, introspector in introspectors:
        group = introspector.getGroupById(group_id)
        if group is None:
            break
    return group
PluggableAuthService.getGroup = getGroup


security.declarePublic("getLocalRolesForDisplay")
def getLocalRolesForDisplay(self, object):
    """This is used for plone's local roles display
    This method returns a tuple (massagedUsername, roles, userType, actualUserName).
    This method is protected by the 'access content information' permission. We may
    change that if it's too permissive...

    A GRUF method originally.
    """
    result = []
    local_roles = object.get_local_roles()   # we don't have a PAS-side way to get this
    for one_user in local_roles:
        username = one_user[0]
        roles = one_user[1]
        userType = 'user'
        if self.getGroup(username):
            userType = 'group'
        result.append((username, roles, userType, username))
    return tuple(result)
PluggableAuthService.getLocalRolesForDisplay = getLocalRolesForDisplay



#################################
# non standard gruf --- junk method  XXX remove me

def _doDelUsers(self, names):
    """Delete one or more users. This should be implemented by subclasses
       to do the actual deleting of users."""
    for name in names:
        self._doDelUser(name)

PluggableAuthService._doDelUsers = _doDelUsers



