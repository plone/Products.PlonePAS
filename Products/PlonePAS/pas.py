"""
pas alterations and monkies
$Id: pas.py,v 1.4 2005/02/02 21:34:08 thraxil Exp $
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

# give pas the userfolder public api
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser
PluggableAuthService.userFolderDelUser = PluggableAuthService._doDelUser
