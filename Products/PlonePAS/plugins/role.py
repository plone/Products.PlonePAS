"""
group aware role manager, returns roles assigned to group a principal
is a member of, in addition to the explicit roles assigned directly
to the principal.

"""

from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Acquisition import aq_parent, aq_inner, aq_get
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile

from zope.interface import implements

from Products.PluggableAuthService.plugins.ZODBRoleManager \
     import ZODBRoleManager

from Products.PlonePAS.utils import getGroupsForPrincipal
from Products.PlonePAS.interfaces.capabilities import IAssignRoleCapability
from Products.PluggableAuthService.permissions import ManageUsers

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
    implements(IAssignRoleCapability)

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
                    if role_id in self._roles:
                        # check if this role is managed by this plugin, and set it
                        role_info = self._roles[ role_id ]

        self._principal_roles[ principal_id ] = tuple(roles)
    assignRolesToPrincipal = postonly(assignRolesToPrincipal)

    security.declarePrivate( 'getRolesForPrincipal' )
    def getRolesForPrincipal(self, principal, request=None):
        """ See IRolesPlugin.
        """
        roles = set([])
        principal_ids = set([])
        # Some services need to determine the roles obtained from groups
        # while excluding the directly assigned roles.  In this case
        # '__ignore_direct_roles__' = True should be pushed in the request.
        request = aq_get(self, 'REQUEST', None)
        if request is None or \
            not request.get('__ignore_direct_roles__', False):
            principal_ids.add(principal.getId())

        # Some services may need the real roles of an user but **not**
        # the ones he got through his groups. In this case, the
        # '__ignore_group_roles__'= True should be previously pushed
        # in the request.
        plugins = self._getPAS()['plugins']
        if request is None or \
            not request.get('__ignore_group_roles__', False):
            principal_ids.update(getGroupsForPrincipal(principal, plugins, request))
        for pid in principal_ids:
            roles.update(self._principal_roles.get(pid, ()))
        return tuple(roles)

    ## implement IAssignRoleCapability

    def allowRoleAssign(self, user_id, role_id):
        """True iff this plugin will allow assigning a certain user a
        certain role.

        Note that at least currently this only checks if the role_id
        exists.  If it exists, this method returns True.  Nothing is
        done with the user_id parameter.  This might be wrong.  See
        http://dev.plone.org/plone/ticket/7762
        """
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


InitializeClass( GroupAwareRoleManager )
