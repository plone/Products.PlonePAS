##############################################################################
#
# Portions Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# Portions Copyright (c) 2005 Plone Foundation. All Rights Reserved.
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
$Id: LocalRolesManager.py,v 1.1 2005/02/06 08:18:52 k_vertigo Exp $
"""

from AccessControl import ClassSecurityInfo
from Globals import DTMLFile, InitializeClass
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin


def manage_addLocalRolesManager( dispatcher, id, title=None, REQUEST=None):
    """
    add a local roles manager
    """

    lrm = LocalRolesManager( id, title )
    dispatcher._setObject( lrm.getId(), lrm)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addLocalRolesManagerForm = DTMLFile('../zmi/LocalRolesManagerForm', globals())

class LocalRolesManager( BasePlugin ):

    meta_type = "Local Roles Manager"

    def getRolesInContext( self, user, object):
        user_id = user.getId()
        group_ids = user.getGroups()

        principal_ids = list( group_ids )
        principal_ids.insert( 0, user_id )

        local ={} 
        object = aq_inner( object )

        while 1:

            local_roles = getattr( object, '__ac_local_roles__', None )

            if local_roles:

                if callable( local_roles ):
                    local_roles = local_roles()

                dict = local_roles or {}

                for principal_id in principal_ids:
                    for role in dict.get( principal_id, [] ):
                        local[ role ] = 1

            inner = aq_inner( object )
            parent = aq_parent( inner )

            if getattr(obj, '__ac_local_roles_block__', None):
                break
                
            if parent is not None:
                object = parent
                continue

            new = getattr( object, 'im_self', None )

            if new is not None:

                object = aq_inner( new )
                continue

            break

        return list( user.getRoles() ) + local.keys()


    def checkLocalRolesAllowed( self, user, object, object_roles ):
        # Still have not found a match, so check local roles. We do
        # this manually rather than call getRolesInContext so that
        # we can incur only the overhead required to find a match.
        inner_obj = aq_inner( object )
        user_id = self.getId()
        # [ x.getId() for x in self.getGroups() ]
        group_ids = self.getGroups()

        principal_ids = list( group_ids )
        principal_ids.insert( 0, user_id )

        while 1:

            local_roles = getattr( inner_obj, '__ac_local_roles__', None )

            if local_roles:

                if callable( local_roles ):
                    local_roles = local_roles()

                dict = local_roles or {}

                for principal_id in principal_ids:

                    local_roles = dict.get( principal_id, [] )

                    for role in object_roles:

                        if role in local_roles:

                            if self._check_context( object ):
                                return 1

                            return 0

            inner = aq_inner( inner_obj )
            parent = aq_parent( inner )

            if getattr(obj, '__ac_local_roles_block__', None):
                break

            if parent is not None:
                inner_obj = parent
                continue

            new = getattr( inner_obj, 'im_self', None )

            if new is not None:
                inner_obj = aq_inner( new )
                continue

            break

        return None        

    

