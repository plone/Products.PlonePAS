##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
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

"""

from AccessControl import ClassSecurityInfo
from Globals import DTMLFile, InitializeClass
from Acquisition import aq_parent, aq_inner

from zope.interface import implementedBy

from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.ZODBRoleManager \
     import ZODBRoleManager

from Products.PlonePAS.utils import unique
from Products.PlonePAS.interfaces.capabilities import IAssignRoleCapability

from Products.PluggableAuthService.permissions import ManageUsers

from AccessControl.requestmethod import postonly

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

    security = ClassSecurityInfo()

    def updateRolesList(self):
        role_holder = aq_parent( aq_inner( self._getPAS() ) )
        for role in getattr( role_holder, '__ac_roles__', () ):
            if role not in ('Anonymous', 'Authenticated') and \
                    role not in self._roles:
                try:
                    self.addRole( role )
                except KeyError:
                    pass


    # don't blow up if manager already exists; mostly for ZopeVersionControl
    def manage_afterAdd( self, item, container ):

        try:
            self.addRole( 'Manager' )
        except KeyError:
            pass

        if item is self:
            self.updateRolesList()


    security.declareProtected( ManageUsers, 'assignRoleToPrincipal' )
    def assignRoleToPrincipal( self, role_id, principal_id, REQUEST=None ):
        try:
            return ZODBRoleManager.assignRoleToPrincipal( self, role_id,
                    principal_id, REQUEST)
        except KeyError:
            # Lazily update our roles list and try again
            self.updateRolesList()
            return ZODBRoleManager.assignRoleToPrincipal( self, role_id,
                    principal_id, REQUEST)


    security.declareProtected( ManageUsers, 'assignRolesToPrincipal' )
    def assignRolesToPrincipal( self, roles, principal_id, REQUEST=None ):
        """ Assign a specific set of roles, and only those roles, to a principal.

        o no return value

        o Raise KeyError if a role_id is unknown.
        """
        for role_id in roles:
            if role_id not in ('Authenticated','Anonymous','Owner'):
                try:
                    role_info = self._roles[ role_id ] # raise KeyError if unknown!
                except KeyError:
                    # Lazily update our roles list and try again
                    self.updateRolesList()
                    role_info = self._roles[ role_id ] # raise KeyError if unknown!


        self._principal_roles[ principal_id ] = tuple(roles)
    assignRolesToPrincipal = postonly(assignRolesToPrincipal)

    security.declarePrivate( 'getRolesForPrincipal' )
    def getRolesForPrincipal( self, principal, request=None ):
        """ See IRolesPlugin.
        """
        roles = []
        principal_ids = [principal.getId()]
        # not all user objects are propertied users with groups support.
        # theres no interface for now - so use an ugly hasattr
        if hasattr(principal, 'getGroups'):
            principal_ids.extend( principal.getGroups() )
        for pid in principal_ids:
            roles.extend( self._principal_roles.get( pid, () ) )
        return tuple( unique( roles ) )

    ## implement IAssignRoleCapability

    def allowRoleAssign(self, user_id, role_id):
        """True iff this plugin will allow assigning a certain user a certain role."""
        present = self.getRoleInfo(role_id)
        if present: return 1   # if we have a role, we can assign it
                               # slightly naive, but should be okay.
        return 0

    def listRoleIds(self):
        self.updateRolesList()
        return ZODBRoleManager.listRoleIds(self)

    def listRoleInfo(self):
        self.updateRolesList()
        return ZODBRoleManager.listRoleInfo(self)

    def getRoleInfo(self, role_id):
        if role_id not in self._roles:
            self.updateRolesList()
        return ZODBRoleManager.getRoleInfo(self, role_id)



classImplements(GroupAwareRoleManager,
                IAssignRoleCapability, *implementedBy(ZODBRoleManager))

InitializeClass( GroupAwareRoleManager )
