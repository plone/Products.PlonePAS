##############################################################################
#
# Copyright (c) 2005 Kapil Thangavelu
# Reserved.
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
$Id: ufactory.py,v 1.3 2005/04/20 21:11:51 jccooper Exp $
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile

from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PluggableAuthService.interfaces.plugins import IUserFactoryPlugin
from Products.PluggableAuthService.interfaces.propertysheets import IPropertySheet
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
#from Products.PluggableAuthService.PluggableAuthService import MANGLE_DELIMITER
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

    security = ClassSecurityInfo()

#    def _safeUnmangleId( self, mangled_id ):
#        """
#        safely unmangle an id
#        """
#        parts = mangled_id.split(MANGLE_DELIMITER, 1)
#        return parts[-1]

#    def getId( self ):
#        """ -> user ID
#        """
#	return self._safeUnmangleId(self._id)
#	#return self._id

#    security.declarePrivate('getQualifiedId')
#    def getQualifiedId( self ):
#        """ -> user source plugin id mangled user id
#        """
#        return self._id

    #################################
    # acquisition aware
    def getPropertySheet( self, id):
        """ -> propertysheet (wrapped if supported)
        """
        sheet = self._propertysheets[ id ]
        try:
            return sheet.__of__( self )
        except AttributeError:
            return sheet

    security.declarePrivate('addPropertySheet')
    def addPropertySheet( self, id, data):
        """ -> add a prop sheet, given data which is either
        a property sheet or a raw mapping.
        """ 
        if IPropertySheet.isImplementedBy( data ):
            sheet = data
        else:
            sheet = UserPropertySheet( id, **data )

        if self._propertysheets.get( id ) is not None:
            raise KeyError, "Duplicate property sheet: %s" % id

        self._propertysheets[ id ] = UserPropertySheet( id, **data )

    security.declarePrivate('getOrderedSheets')
    def getOrderedPropertySheets(self):
        # ordered
        source_provider_keys = [plugin_id for plugin_id, plugin in self.acl_users.plugins.listPlugins( IPropertiesPlugin )]
        user_provider_keys = self.listPropertysheets()
        sheets = [ self.getPropertysheet(pk) for pk in source_provider_keys if pk in user_provider_keys]
        return sheets       

#################################
# local roles plugin type delegation - currently disabled    

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


InitializeClass( PloneUser )

