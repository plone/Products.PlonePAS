"""
pas alterations and monkies
$Id: pas.py,v 1.16 2005/02/24 15:13:31 k_vertigo Exp $
"""
import sys
from sets import Set

from Acquisition import aq_inner, aq_parent
from AccessControl.PermissionRole import _what_not_even_god_should_do

from Products.PluggableAuthService.PropertiedUser import \
     PropertiedUser
from Products.PluggableAuthService.PluggableAuthService import \
     PluggableAuthService, MANGLE_DELIMITER, _SWALLOWABLE_PLUGIN_EXCEPTIONS, LOG, BLATHER
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin, IAuthenticationPlugin
from Products.PlonePAS.interfaces.plugins import IUserManagement, ILocalRolesPlugin


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
# XXX need to security restrict these methods, no base class sec decl
#PluggableAuthService.userFolderDelUser__roles__ = 
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

    roles_not_set = sroles.difference( Set( roles ) )
    
    if not len( roles_not_set ) == 0:
        raise RuntimeError("not all roles were set - %s"%roles_not_set)

    return True

PluggableAuthService._doChangeUser = _doChangeUser
# XXX need to security restrict these methods, no base class sec decl
#PluggableAuthService.userFolderEditUser__roles__ = ()
PluggableAuthService.userFolderEditUser = PluggableAuthService._doChangeUser 

# ttw alias
# XXX need to security restrict these methods, no base class sec decl
#PluggableAuthService.userFolderAddUser__roles__ = ()
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser



#################################
# non standard gruf --- junk method  XXX remove me

def _doDelUsers(self, names):
    """Delete one or more users. This should be implemented by subclasses
       to do the actual deleting of users."""
    for name in names:
        self._doDelUser(name)

PluggableAuthService._doDelUsers = _doDelUsers



