"""
pas alterations and monkies
$Id: pas.py,v 1.7 2005/02/03 00:09:47 k_vertigo Exp $
"""

from Products.PluggableAuthService.PropertiedUser import \
     PropertiedUser

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


PropertiedUser._safeUnmangleId = _safeUnmangleId
PropertiedUser.getId = getId
PropertiedUser.getQualifiedId = getQualifiedId

from Products.PluggableAuthService.PluggableAuthService import \
     PluggableAuthService, MANGLE_DELIMITER
from Products.PlonePAS.interfaces.plugins import IUserDeleterPlugin

def _doDelUser(self, login):
    """ given a login, hand off to a deleter plugin if available;
    return a boolean"""

    plugins = self._getOb( 'plugins' )
    userdeleters = plugins.listPlugins( IUserDeleterPlugin )

    if not (userdeleters):
        raise NotImplementedError( "There is no plugin that can "
                                   " delete users." )

    for userdeleter_id, userdeleter in userdeleters:
        if userdeleter.doDelUser( login ):
            return True
PluggableAuthService._doDelUser = _doDelUser

def _doDelUsers(self, names):
    """Delete one or more users. This should be implemented by subclasses
       to do the actual deleting of users."""
    for name in names:
        self._doDelUser(name)

PluggableAuthService._doDelUsers = _doDelUsers


def getUserSourceId(self,):
    """
    getUserSourceId(self,) => string
    Return the GRUF's GRUFUsers folder used to fetch this user.
    """
    return self._source_id

PluggableAuthService.getUserSourceId = getUserSourceId

def userFolderAddGroup(self, groupname, roles = [], groups = (), **kw):
    """
    Add a group.
    """
    return self._doAddGroup(groupname, roles, groups, **kw)

PluggableAuthService.userFolderAddGroup = userFolderAddGroup

def _doAddGroup(self, name, roles, groups = (), **kw):
    """
    Create a new group. Password will be randomly created, and domain will be None.
    Supports nested groups.
    """
PluggableAuthService._doAddGroup = _doAddGroup

def _updateUser(self, name, password = None, roles = None, domains = None, groups = None):
    """
    _updateUser(self, name, password = None, roles = None, domains = None, groups = None)
    Front-end to _doChangeUser, but with a better default value support.
    We guarantee that None values will let the underlying UF keep the original ones.
    This is not true for the password: some buggy UF implementation may not
    handle None password correctly :-(
    """

PluggableAuthService._updateUser = _updateUser


# give pas the userfolder public api
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser
PluggableAuthService.userFolderDelUser = PluggableAuthService._doDelUser
PluggableAuthService.userFolderEditUser = PluggableAuthService._updateUser
