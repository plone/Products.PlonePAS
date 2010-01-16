"""
ZODB Group Implementation with basic introspection and
management (ie. rw) capabilities.

"""

import logging
from BTrees.OOBTree import OOBTree, OOSet
from App.special_dtml import DTMLFile
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements

from Products.PluggableAuthService.PluggableAuthService import _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.plugins.ZODBGroupManager import ZODBGroupManager
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from Products.PluggableAuthService.utils import createViewName

from Products.PlonePAS.interfaces.group import IGroupManagement, IGroupIntrospection
from Products.PlonePAS.interfaces.capabilities import IGroupCapability
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from ufactory import PloneUser

manage_addGroupManagerForm = DTMLFile("../zmi/GroupManagerForm", globals())
logger = logging.getLogger('PlonePAS')

def manage_addGroupManager(self, id, title='', RESPONSE=None):
    """
    Add a zodb group manager with management and introspection
    capabilities to pas.
    """
    grum = GroupManager(id, title)

    self._setObject(grum.getId(), grum)

    if RESPONSE is not None:
        return RESPONSE.redirect('manage_workspace')


class GroupManager(ZODBGroupManager):

    meta_type = "Group Manager"
    security = ClassSecurityInfo()

    implements(IGroupManagement, IGroupIntrospection, IGroupCapability,
               IDeleteCapability)

    def __init__(self, *args, **kw):
        ZODBGroupManager.__init__(self, *args, **kw)
        self._group_principal_map = OOBTree() # reverse index of groups->principal

    #################################
    # overrides to ease group principal lookups for introspection api

    def addGroup(self, group_id, *args, **kw):
        ZODBGroupManager.addGroup(self, group_id, *args, **kw)
        self._group_principal_map[ group_id ] = OOSet()
        return True

    def removeGroup(self, group_id):
        ZODBGroupManager.removeGroup(self, group_id)
        del self._group_principal_map[ group_id ]
        return True

    def addPrincipalToGroup(self, principal_id, group_id):
        ZODBGroupManager.addPrincipalToGroup(self, principal_id, group_id)
        self._group_principal_map[ group_id ].insert(principal_id)
        return True

    def removePrincipalFromGroup(self, principal_id, group_id):
        already = ZODBGroupManager.removePrincipalFromGroup(self, principal_id, group_id)
        if already: self._group_principal_map[ group_id ].remove(principal_id)
        return True

    #################################
    # overrides for api matching/massage

    def updateGroup(self, group_id, title=None, description=None):
        ZODBGroupManager.updateGroup(self, group_id, title=title, description=description)
        return True

    #################################
    # introspection interface

    def getGroupById(self, group_id, default=None):
        plugins = self._getPAS()._getOb('plugins')
        title = None
        if group_id not in self.getGroupIds():
            return default

        return self._findGroup(plugins, group_id, title)

    def getGroups(self):
        return map(self.getGroupById, self.getGroupIds())

    def getGroupIds(self):
        return self.listGroupIds()

    def getGroupMembers(self, group_id):
        return tuple(self._group_principal_map.get(group_id,()))

    #################################
    # capabilties interface impls.

    security.declarePublic('allowDeletePrincipal')
    def allowDeletePrincipal(self, principal_id):
        """True iff this plugin can delete a certain group.
        This is true if this plugin manages the group.
        """
        if self._groups.get(principal_id) is not None:
            return 1
        return 0

    def getGroupInfo( self, group_id ):
        """Over-ride parent to not explode when getting group info dict by group id."""
        return self._groups.get(group_id,None)

    def allowGroupAdd(self, user_id, group_id):
        """True iff this plugin will allow adding a certain user to a certain group."""
        present = self.getGroupInfo(group_id)
        if present: return 1   # if we have a group, we can add users to it
                                # slightly naive, but should be okay.
        return 0

    def allowGroupRemove(self, user_id, group_id):
        """True iff this plugin will allow removing a certain user from a certain group."""
        present = self.getGroupInfo(group_id)
        if not present: return 0   # if we don't have a group, we can't do anything

        group_members = self.getGroupMembers(group_id)
        if user_id in group_members: return 1
        return 0

    #################################
    # group wrapping mechanics

    security.declarePrivate('_createGroup')
    def _createGroup(self, plugins, group_id, name):
        """ Create group object. For users, this can be done with a
        plugin, but I don't care to define one for that now. Just uses
        PloneGroup.  But, the code's still here, just commented out.
        This method based on PluggableAuthervice._createUser
        """
        return PloneGroup(group_id, name).__of__(self)

    security.declarePrivate('_findGroup')
    def _findGroup(self, plugins, group_id, title=None, request=None):
        """ group_id -> decorated_group
        This method based on PluggableAuthService._findGroup
        """

        view_name = '_findGroup-%s' % group_id
        keywords = { 'group_id' : group_id
                   , 'title' : title
                   }

        group = self._createGroup(plugins, group_id, title)

        propfinders = plugins.listPlugins(IPropertiesPlugin)
        for propfinder_id, propfinder in propfinders:

            data = propfinder.getPropertiesForUser(group, request)
            if data:
                group.addPropertysheet(propfinder_id, data)

        groups = self._getPAS()._getGroupsForPrincipal(group, request
                                            , plugins=plugins)
        group._addGroups(groups)

        rolemakers = plugins.listPlugins(IRolesPlugin)

        for rolemaker_id, rolemaker in rolemakers:
            roles = rolemaker.getRolesForPrincipal(group, request)
            if roles:
                group._addRoles(roles)

        group._addRoles(['Authenticated'])

        return group.__of__(self)

    security.declarePrivate('_verifyGroup')
    def _verifyGroup(self, plugins, group_id=None, title=None):

        """ group_id -> boolean
        This method based on PluggableAuthService._verifyUser
        """
        criteria = {}

        if group_id is not None:
            criteria[ 'id' ] = group_id
            criteria[ 'exact_match' ] = True

        if title is not None:
            criteria[ 'title' ] = title

        if criteria:
            view_name = createViewName('_verifyGroup', group_id)
            enumerators = plugins.listPlugins(IGroupEnumerationPlugin)

            for enumerator_id, enumerator in enumerators:
                try:
                    info = enumerator.enumerateGroups(**criteria)

                    if info:
                        return info[0]['id']

                except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                    logger.info(
                        'PluggableAuthService: GroupEnumerationPlugin %s error',
                        enumerator_id, exc_info=1)

        return 0


InitializeClass(GroupManager)


class PloneGroup(PloneUser):
    """Plone expects a user to come, with approximately the same
    behavior as a user.
    """

    security = ClassSecurityInfo()
    _isGroup = True

    def getId(self, unprefixed=None):
        """ -> user ID
        Modified to accept silly GRUF param.
        """
        return self._id

    security.declarePrivate("getMemberIds")
    def getMemberIds(self, transitive = 1):
        """Return member ids of this group, including or not
        transitive groups.
        """
        # acquired from the groups_source
        plugins = self._getPAS().plugins
        introspectors = plugins.listPlugins(IGroupIntrospection)
        members=[]
        for iid, introspector in introspectors:
            try:
                members.extend(list(introspector.getGroupMembers(self.getId())))
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                logger.info(
                    'PluggableAuthService: getGroupMembers %s error',
                    iid, exc_info=1)

        return members


    security.declarePublic('addMember')
    def addMember(self, id):
        """Add the existing member with the given id to the group
        """
        self.addPrincipalToGroup(id, self.getId())

    security.declarePublic('removeMember')
    def removeMember(self, id):
        """Remove the member with the provided id from the group.
        """
        self.removePrincipalFromGroup(id, self.getId())

    security.declarePublic('getRolesInContext')
    def getRolesInContext(self, object):
        """Since groups can't actually log in, do nothing.
        """
        return []

    security.declarePublic('allowed')
    def allowed(self, object, object_roles=None):
        """Since groups can't actually log in, do nothing.
        """
        return 0

InitializeClass(PloneGroup)
