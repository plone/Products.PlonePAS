"""
pas alterations and monkies
$Id: pas.py,v 1.3 2005/02/02 05:28:59 bcsaller Exp $
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

# give pas the userfolder public api
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser
PluggableAuthService.userFolderDelUser = PluggableAuthService._doDelUser
