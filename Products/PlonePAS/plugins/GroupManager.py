"""

ZODB Group Implementation with basic introspection and
management (ie. rw) capabilities.

$Id: GroupManager.py,v 1.1 2005/02/04 23:23:31 k_vertigo Exp $
"""

from BTrees.OOBTree import OOBTree, OOSet
from Globals import DTMLFile

from Products.PluggableAuthService.plugins.ZODBGroupManager import ZODBGroupManager
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin, IGroupEnumerationPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement, IGroupIntrospection

manage_addGroupManagerForm = DTMLFile("../zmi/GroupManagerForm", globals())

def manage_addGroupManager(self, id, title='', RESPONSE=None):
    """
    add a zodb group manager with management and introspection
    capabilities to pas.
    """
    grum = GroupManager( id, title )

    self._setObject( grum.getId(), grum )

    if RESPONSE is not None:
        return RESPONSE.redirect('manage_workspace')


class GroupManager( ZODBGroupManager ):
    
    meta_type = "Group Manager"

    __implements__ = ( IGroupsPlugin, IGroupEnumerationPlugin,
                       IGroupManagement, IGroupIntrospection )


    def __init__(self, *args, **kw):
        ZODBGroupManager.__init__(self, *args, **kw)
        self._group_principal_map = OOBTree() # reverse index of groups->principal

    #################################
    # overrides to ease group principal lookups for introspection api
    
    def addGroup(self, group_id, *args, **kw):
        ZODBGroupManager.addGroup( self, group_id, *args, **kw)
        self._group_principal_map[ group_id ] = OOSet()
        
    def removeGroup(self, group_id):
        ZODBGroupManager.removeGroup( self, group_id )
        del self._group_principal_map[ group_id ]

    def addPrincipalToGroup(self, principal_id, group_id):
        ZODBGroupManager.addPrincipalToGroup( self, principal_id, group_id)
        self._group_principal_map[ group_id ].insert( principal_id )

    def removePrincipalFromGroup(self, principal_id, group_id):
        ZODBGroupManager.removePrincipalFromGroup( self, principal_id, group_id)
        self._group_principal_map[ group_id ].remove( principal_id )

    #################################
    # overrides for api matching/massage

    def updateGroup(self, group_id, **kw):
        kw['title'].setdefault('')
        kw['description'].setdefault('')
        ZODBGroupManager.updateGroup(self, group_id, **kw)

    #################################
    # introspection interface
    
    def getGroupById(self, group_id):
        return self.getGroupInfo( group_id )

    def getGroups(self):
        return map( self.getGroupById, self.getGroupIds() )

    def getGroupIds(self):
        return self.listGroupIds()

    def getGroupMembers(self, group_id):
        return tuple( self._group_principal_map[ group_id ] )
        
