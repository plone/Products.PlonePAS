"""
$Id: PloneUserFactory.py,v 1.2 2005/05/24 17:50:07 dreamcatcher Exp $
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile

from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.interfaces.plugins import IUserFactoryPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PlonePAS.utils import unique

manage_addPloneUserFactoryForm = DTMLFile("../zmi/PloneUserFactoryForm", globals() )

def manage_addPloneUserFactory(self, id, title='', RESPONSE=None):
    """
    add a plone user factory
    """

    puf = PloneUserFactory( id, title )
    self._setObject( puf.getId(), puf )

    if RESPONSE is not None:
        return RESPONSE.redirect('manage_workspace')


class PloneUserFactory( BasePlugin ):

    meta_type = "Plone User Factory"

    __implements__ = ( IUserFactoryPlugin, )

    def __init__(self, id, title=''):
        self.id = id
        self.title = title or self.meta_type

    def createUser( self, user_id, name ):

        return PloneUser( user_id, name )

InitializeClass( PloneUserFactory )


class PloneUser( PropertiedUser ):

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

    def __getRolesInContext(self, object):
        lrmanagers = aq_parent( aq_inner( self ) ).plugins.listPlugins( ILocalRolesPlugin )
        roles = []
        for lrid, lrmanager in lrmanagers:
            roles.extend( lrmanager.getRolesInContext( self, object ) )
        return unique( roles )

    def __allowed( self, object, object_roles = None ):
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
