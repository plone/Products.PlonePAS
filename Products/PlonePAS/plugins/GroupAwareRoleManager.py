"""
group aware role manager, returns roles assigned to group a principal
is a member of, in addition to the explicit roles assigned directly
to the principal.

$Id: GroupAwareRoleManager.py,v 1.1 2005/02/03 19:43:21 k_vertigo Exp $
"""

from AccessControl import ClassSecurityInfo
from Globals import DTMLFile, InitializeClass
from Products.PluggableAuthService.plugins.ZODBRoleManager \
     import ZODBRoleManager


def unique( iterable ):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()

def manage_addGroupAwareRoleManager( self, id, title, RESPONSE=None):
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
            
