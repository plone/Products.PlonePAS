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

acts as a bridge between gruf and pas. fufilling group, role, and principal
management plugin functionalities within pas via delegation to a contained gruf
instance.

"""

from Globals import DTMLFile, InitializeClass

from zope.interface import implementedBy

from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.DelegatingMultiPlugin \
     import DelegatingMultiPlugin
from Products.PluggableAuthService.interfaces import plugins
from AccessControl.requestmethod import postonly


def manage_addGRUFBridge(self, id, title='', RESPONSE=None ):
    """
    add gruf bridge
    """

    bridge = GRUFBridge( id, title='')
    self._setObject( id, bridge )

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')


manage_addGRUFBridgeForm = DTMLFile('../zmi/GRUFBridgeForm', globals())

class GroupFilter( object ):

    def __init__(self,  id, exact_match, **kw):
        if isinstance( id, str):
            id = [ id ]
        self.group_ids = id
        self.exact_match = not not exact_match

    def __call__(self, group):
        tid = group.getId()
        if self.exact_match:
            if tid in self.group_ids:
                return True
            return False
        for value in self.group_ids:
            if value.find( tid ) >= 0:
                return True


class GRUFBridge( DelegatingMultiPlugin ):

    meta_type = "GRUF Bridge"

    def manage_afterAdd(self, item, container):
        self.manage_addProduct['GroupUserFolder'].manage_addGroupUserFolder()

    def _getUserFolder(self):
        return self.acl_users

    #################################
    # group interface implementation

    # plugins.IGroupsEnumerationPlugin
    def enumerateGroups( self,
                         id=None,
                         title=None,
                         exact_match=False,
                         sort_by=None,
                         max_results=None,
                         **kw
                         ):

        gruf = self._getUserFolder()
        groups = gruf.getGroups()
        filter = GroupFilter( id, exact_match, **kw )
        if max_results is None:
            max_results = -1
        return [self.getGroupInfo( group ) for group in groups if filter(group)][:max_results]

    # plugins.IGroupsPlugin
    def getGroupsForPrincipal( self, principal, request=None ):
        gruf = self._getUserFolder()
        pid = self._demangle( principal.getId() )
        gruf_principal = gruf.getUser( pid )
        return gruf_principal.getGroupsWithoutPrefix()

    #################################
    # group management

    # gruf assumes it is the canonical source for both users and groups
    def addGroup(self, group_id, REQUEST=None):
        self._getUserFolder().userFolderAddGroup( group_id, (), () )
        return True
    addGroup = postonly(addGroup)

    def addPrincipalToGroup(self, principal_id, group_id, REQUEST=None):
        group = self._getUserFolder().getGroupById( group_id )
        group.addMember( principal_id )
    addPrincipalToGroup = postonly(addPrincipalToGroup)

    # XXX need to fix this api, its too ambigious
    def updateGroup(self, group_id, REQUEST=None, **kw):
        pass
    updateGroup = postonly(updateGroup)

    def setRolesForGroup(self, group_id, roles=(), REQUEST=None):
        # doing it this way will lose subgroups..
        self._getUserFolder().userFolderEditGroup( group_id, roles )
    setRolesForGroup = postonly(setRolesForGroup)

    def removeGroup(self, group_id, REQUEST=None):
        return self._getUserFolder().userFolderDelGroups( (group_id, ) )
    removeGroup = postonly(removeGroup)

    def removePrincipalFromGroup(self, principal_id, group_id, REQUEST=None):
        group = self._getUserFolder().getGroupById( group_id )
        group.removeMember( principal_id )
        return True
    removePrincipalFromGroup = postonly(removePrincipalFromGroup)

    #################################
    # group introspection

    def getGroupById( self, group_id ):
        return self._getUserFolder().getGroupById( group_id )

    def getGroupIds(self):
        # gruf returns these prefixed
        return self._getUserFolder().getGroupIds()

    def getGroups(self):
        return self._getUserFolder().getGroups()

    def getGroupMembers(self, group_id):
        return self._getUserFolder().getMemberIds(group_id)

    #################################
    def getGroupInfo(self, group):
        url = group.absolute_url()
        return {
            'id' : group.getId(),
            'pluginid' : self.getId(),
            'members_url' : url,
            'properties_url' : url,
            }

    def _demangle(self, princid):
        unmangle_fn = self.aq_acquire('_unmangleId') # acquire from PAS
        unmangled_princid = unmangle_fn(princid)[-1]
        return unmangled_princid

classImplements(GRUFBridge,
                plugins.IGroupsPlugin, plugins.IGroupEnumerationPlugin,
                *implementedBy(DelegatingMultiPlugin))

InitializeClass(GRUFBridge)
