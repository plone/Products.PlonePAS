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
group aware role manager, returns roles assigned to group a principal
is a member of, in addition to the explicit roles assigned directly
to the principal.

$Id: role.py,v 1.1 2005/02/24 15:22:48 k_vertigo Exp $
"""

from AccessControl import ClassSecurityInfo
from Globals import DTMLFile, InitializeClass
from Products.PluggableAuthService.plugins.ZODBRoleManager \
     import ZODBRoleManager
from Products.PlonePAS.utils import unique

def manage_addGroupAwareRoleManager( self, id, title='', RESPONSE=None):
    """
    this is a doc string
    """
    garm = GroupAwareRoleManager( id, title )
    self._setObject( garm.getId(), garm)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addGroupAwareRoleManagerForm = DTMLFile(
    '../zmi/GroupAwareRoleManagerForm', globals())

class GroupAwareRoleManager( ZODBRoleManager ):

    meta_type = "Group Aware Role Manager"
    __implements__ = ZODBRoleManager.__implements__

    security = ClassSecurityInfo()

    security.declarePrivate( 'getRolesForPrincipal' )
    def getRolesForPrincipal( self, principal, request=None ):
        """ See IRolesPlugin.
        """
        roles = []
        principal_ids = [principal.getId()]
        principal_ids.extend( principal.getGroups() )
        for pid in principal_ids:
            roles.extend( self._principal_roles.get( pid, () ) )
        return tuple( unique( roles ) )

InitializeClass( GroupAwareRoleManager )

