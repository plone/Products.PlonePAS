"""
pas alterations and monkies
$Id: pas.py,v 1.11 2005/02/06 08:18:49 k_vertigo Exp $
"""

from sets import Set

from Acquisition import aq_inner, aq_parent
from AccessControl.PermissionRole import _what_not_even_god_should_do

from Products.PluggableAuthService.PropertiedUser import \
     PropertiedUser
from Products.PluggableAuthService.PluggableAuthService import \
     PluggableAuthService, MANGLE_DELIMITER
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PlonePAS.interfaces.plugins import IUserManagement, ILocalRolesPlugin

def unique( iterable ):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()

#################################
# pas user monkies

def _safeUnmangleId(self, mangled_id):
    """
    safely unmangle an id
    """
    parts = mangled_id.split(MANGLE_DELIMITER, 1)
    return parts[-1]


def getId( self ):
    """ -> user ID
    """
    return self._safeUnmangleId(self._id)

def getQualifiedId(self):
    return self._id

def getRolesInContext(self, object):
    lrmanagers = aq_parent( aq_inner( self ) ).plugins.listPlugins( ILocalRolesPlugin )
    roles = []
    for lrid, lrmanager in lrmanagers:
        roles.extend( lrmanager.getRolesInContext( self, object ) )
    return unique( roles )

def allowed( self, object, object_roles = None ):
    if object_roles is _what_not_even_god_should_do:
        return 0

    # Short-circuit the common case of anonymous access.
    if object_roles is None or 'Anonymous' in object_roles:
        return 1

    # Provide short-cut access if object is protected by 'Authenticated'
    # role and user is not nobody
    if 'Authenticated' in object_roles and (
        self.getUserName() != 'Anonymous User'):
        return 1

    # Check for ancient role data up front, convert if found.
    # This should almost never happen, and should probably be
    # deprecated at some point.
    if 'Shared' in object_roles:
        object_roles = self._shared_roles(object)
        if object_roles is None or 'Anonymous' in object_roles:
            return 1

    # Check for a role match with the normal roles given to
    # the user, then with local roles only if necessary. We
    # want to avoid as much overhead as possible.
    user_roles = self.getRoles()
    for role in object_roles:
        if role in user_roles:
            if self._check_context(object):
                return 1
            return None

    # check for local roles
    lrmanagers = aq_parent( aq_inner( self ) ).plugins.listPlugins( ILocalRolesPlugin )

    for lrid, lrmanager in lrmanagers:
        access_allowed = lrmanager.allowed( self, object, object_roles )
        # return values
        # 0,1,None - 1 success, 0 object context violation - None - failure
        if access_allowed is None: 
            continue
        return access_allowed

    return None

PropertiedUser._safeUnmangleId = _safeUnmangleId
PropertiedUser.getId = getId
PropertiedUser.getQualifiedId = getQualifiedId
#PropertiedUser.getRolesInContext = getRolesInContext
#PropertiedUser.allowed = allowed

#################################
# pas folder monkies - standard zope user folder api

def _doDelUser(self, login):
    """
    given a login, hand off to a deleter plugin if available;
    return a boolean
    """

    plugins = self._getOb( 'plugins' )
    userdeleters = plugins.listPlugins( IUserManagement )

    if not userdeleters:
        raise NotImplementedError( "There is no plugin that can "
                                   " delete users." )

    for userdeleter_id, userdeleter in userdeleters:
        if userdeleter.doDelUser( login ):
            return True
        
PluggableAuthService._doDelUser = _doDelUser
PluggableAuthService.userFolderDelUser = PluggableAuthService._doDelUser

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
        if manager.doChangeUser( principal_id, password ):
            modified = True

    if not modified:
        raise RuntimeError("no user management plugins were able to successfully modify the user")

    sroles = Set() # keep track that we set all the requested roles
    for rid, rmanager in rmanagers:
        
        for role in roles:
            if rmanager.addRoleToPrincipal( principal_id, role):
                sroles.add( role )

    roles_not_set = sroles.intersection( Set( roles ) )
    
    if not len( roles_not_set ) == 0:
        raise RuntimeError("not all roles were set - %s"%roles_not_set)

    return True

PluggableAuthService._doChangeUser = _doChangeUser
PluggableAuthService.userFolderEditUser = PluggableAuthService._doChangeUser 


#
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser

#################################
# non standard gruf --- junk method  XXX remove me

def _doDelUsers(self, names):
    """Delete one or more users. This should be implemented by subclasses
       to do the actual deleting of users."""
    for name in names:
        self._doDelUser(name)

PluggableAuthService._doDelUsers = _doDelUsers



