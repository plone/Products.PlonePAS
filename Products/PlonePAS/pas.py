"""
pas alterations and monkies
$Id: pas.py,v 1.2 2005/02/02 00:10:18 whit537 Exp $
"""

from Products.PluggableAuthService.PluggableAuthService import PluggableAuthService

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