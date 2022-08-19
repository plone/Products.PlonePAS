from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl import Permissions
from AccessControl import Unauthorized
from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from Products.PlonePAS.interfaces.capabilities import IManageCapabilities
from Products.PlonePAS.interfaces.group import IGroupData
from Products.PlonePAS.interfaces.group import IGroupDataTool
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PlonePAS.tools.memberdata import MemberData
from Products.PlonePAS.utils import CleanupTemp
from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService
from Products.PluggableAuthService.PluggableAuthService import (
    _SWALLOWABLE_PLUGIN_EXCEPTIONS,
)
from zope.interface import implementer
from ZPublisher.Converters import type_converters

import logging


logger = logging.getLogger("PlonePAS")
_marker = object()


class GroupDataError(Exception):
    pass


@implementer(IGroupDataTool)
class GroupDataTool(UniqueObject, SimpleItem, PropertyManager):
    """This tool wraps group objects, allowing transparent access to
    properties.
    """

    id = "portal_groupdata"
    meta_type = "PlonePAS GroupData Tool"
    toolicon = "tool.gif"

    _v_temps = None
    _properties = ({"id": "title", "type": "string", "mode": "wd"},)
    security = ClassSecurityInfo()

    def __init__(self):
        self._members = OOBTree()
        # Create the default properties.
        self._setProperty("description", "", "text")
        self._setProperty("email", "", "string")

    def wrapGroup(self, g):
        """Returns an object implementing the GroupData interface."""

        gid = g.getId()
        members = self._members
        if gid not in members:
            # Get a temporary member that might be
            # registered later via registerMemberData().
            temps = self._v_temps
            if temps is not None and gid in temps:
                portal_group = temps[gid]
            else:
                base = aq_base(self)
                portal_group = GroupData(base, gid)
                if temps is None:
                    self._v_temps = {gid: portal_group}
                    if hasattr(self, "REQUEST"):
                        self.REQUEST._hold(CleanupTemp(self))
                else:
                    temps[gid] = portal_group
        else:
            portal_group = members[gid]
        # Return a wrapper with self as containment and
        # the user as context.
        return portal_group.__of__(self).__of__(g)

    @security.private
    def registerGroupData(self, g, id):
        """
        Adds the given member data to the _members dict.
        This is done as late as possible to avoid side effect
        transactions and to reduce the necessary number of
        entries.
        """
        self._members[id] = aq_base(g)


InitializeClass(GroupDataTool)
registerToolInterface("portal_groupdata", IGroupDataTool)


@implementer(IGroupData, IManageCapabilities)
class GroupData(SimpleItem):

    security = ClassSecurityInfo()

    id = None
    _tool = None

    def __init__(self, tool, id):
        self.id = id
        # Make a temporary reference to the tool.
        # The reference will be removed by notifyModified().
        self._tool = tool

    def _getGRUF(
        self,
    ):
        return self.acl_users

    @security.private
    def notifyModified(self):
        # Links self to parent for full persistence.
        tool = getattr(self, "_tool", None)
        if tool is not None:
            del self._tool
            tool.registerGroupData(self, self.getId())

    @security.public
    def getGroup(self):
        """Returns the actual group implementation. Varies by group
        implementation (GRUF/Nux/et al). In GRUF this is a user object."""
        # The user object is our context, but it's possible for
        # restricted code to strip context while retaining
        # containment.  Therefore we need a simple security check.
        parent = aq_parent(self)
        bcontext = aq_base(parent)
        bcontainer = aq_base(aq_parent(aq_inner(self)))
        if bcontext is bcontainer or not hasattr(bcontext, "getUserName"):
            raise GroupDataError("Can't find group data")
        # Return the user object, which is our context.
        return parent

    def getTool(self):
        return aq_parent(aq_inner(self))

    @security.public
    def getGroupMemberIds(self):
        """
        Return a list of group member ids
        """
        return [member.getMemberId() for member in self.getGroupMembers()]

    @security.public
    def getAllGroupMemberIds(self):
        """
        Return a list of group member ids
        """
        return [member.getMemberId() for member in self.getAllGroupMembers()]

    @security.public
    def getGroupMembers(self):
        """
        Returns a list of the portal_memberdata-ish members of the group.
        This doesn't include TRANSITIVE groups/users.
        """
        md = self.portal_memberdata
        gtool = self.portal_groups
        ret = []
        for u_name in gtool.getGroupMembers(self.getId()):
            usr = self._getGRUF().getUserById(u_name)
            # getUserById from
            #   Products.PluggableAuthService.PluggableAuthService
            # The returned object is not wrapped, we wrapped it below
            if not usr:
                usr = self._getGRUF().getGroupById(u_name)
                # getGroupById from Products.PlonePAS.pas
                # The returned object is already wrapped
                if not usr:
                    logger.debug(f"Group has a non-existing principal {u_name}")
                    continue
                ret.append(usr)
            else:
                ret.append(md.wrapUser(usr))
        return ret

    @security.public
    def getAllGroupMembers(self):
        """
        Returns a list of the portal_memberdata-ish members of the group.
        This will include transitive groups / users
        """
        md = self.portal_memberdata
        ret = []
        for u_name in self.getGroup().getMemberIds():
            usr = self._getGRUF().getUserById(u_name)
            if not usr:
                usr = self._getGRUF().getGroupById(u_name)
                if not usr:
                    logger.debug(f"Group has a non-existing principal {u_name}")
                    continue
                ret.append(usr)
            else:
                ret.append(md.wrapUser(usr))
        return ret

    def _getGroup(self):
        """Get the underlying group object in a PAS-acceptable way.
        (I don't even know why there's the two different ways for GRUF. Speed?)
        """
        return self.getGroup()

    @security.private
    def canAdministrateGroup(self):
        """
        Return true if the #current# user can administrate this group
        """
        user = getSecurityManager().getUser()
        tool = self.getTool()
        portal = getToolByName(tool, "portal_url").getPortalObject()

        # Has manager users pemission?
        if user.has_permission(Permissions.manage_users, portal):
            return True

        # Is explicitly mentioned as a group administrator?
        managers = self.getProperty("delegated_group_member_managers", ())
        if user.getId() in managers:
            return True

        # Belongs to a group which is explicitly mentionned as a group
        # administrator
        meth = getattr(user, "getAllGroupNames", None)
        if meth:
            groups = meth()
        else:
            groups = ()
        for v in groups:
            if v in managers:
                return True

        # No right to edit this: we complain.
        return False

    @security.public
    @postonly
    def addMember(self, id, REQUEST=None):
        """Add the existing member with the given id to the group"""
        if not self.canAdministrateGroup():
            raise Unauthorized("You cannot add a member to the group.")

        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            try:
                if manager.addPrincipalToGroup(id, self.getId()):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                pass

    @security.public
    @postonly
    def removeMember(self, id, REQUEST=None):
        """Remove the member with the provided id from the group."""
        if not self.canAdministrateGroup():
            raise Unauthorized("You cannot remove a member from the group.")

        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            try:
                if manager.removePrincipalFromGroup(id, self.getId()):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                pass

    @security.protected(Permissions.manage_users)
    def setProperties(self, properties=None, **kw):
        """Allows the manager group to set his/her own properties.
        Accepts either keyword arguments or a mapping for the "properties"
        argument.
        """
        if properties is None:
            properties = kw
        return self.setGroupProperties(properties)

    @security.protected(Permissions.manage_users)
    def setGroupProperties(self, mapping):
        """PAS-specific method to set the properties of a group."""
        sheets = None

        if not IPluggableAuthService.providedBy(self.acl_users):
            # Defer to base impl in absence of PAS, a PAS group, or
            # property sheets
            return self._gruf_setGroupProperties(mapping)
        else:
            # It's a PAS! Whee!
            group = self.getGroup()
            sheets = getattr(group, "getOrderedPropertySheets", lambda: [])()

            # We won't always have PlonePAS groups, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                # Defer to base impl if we have a PAS but no property
                # sheets.
                return self._gruf_setGroupProperties(mapping)

        # If we got this far, we have a PAS and some property sheets.
        # XXX track values set to defer to default impl
        # property routing?
        modified = False
        for k, v in mapping.items():
            for sheet in sheets:
                if not sheet.hasProperty(k):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    sheet.setProperty(group, k, v)
                    modified = True
                else:
                    raise RuntimeError(
                        "Mutable property provider " "shadowed by read only provider"
                    )
        if modified:
            self.notifyModified()

    def _gruf_setGroupProperties(self, mapping):
        """Sets the properties of the member."""
        # Sets the properties given in the MemberDataTool.
        tool = self.getTool()
        for id in tool.propertyIds():
            if id in mapping:
                if id not in self.__class__.__dict__:
                    value = mapping[id]
                    if isinstance(value, str):
                        proptype = tool.getPropertyType(id) or "string"
                        if proptype in type_converters:
                            value = type_converters[proptype](value)
                    setattr(self, id, value)

        # Hopefully we can later make notifyModified() implicit.
        self.notifyModified()

    @security.public
    def getProperties(self):
        """Return the properties of this group. Properties are as usual
        in Zope.
        """
        tool = self.getTool()
        ret = {}
        for pty in tool.propertyIds():
            try:
                ret[pty] = self.getProperty(pty)
            except ValueError:
                # We ignore missing ptys
                continue
        return ret

    @security.public
    def getProperty(self, id, default=None):
        """PAS-specific method to fetch a group's properties. Looks
        through the ordered property sheets.
        """
        group = self.getGroup()
        sheets = getattr(group, "getOrderedPropertySheets", lambda: [])()

        # If we made this far, we found a PAS and some property sheets.
        for sheet in sheets:
            if sheet.hasProperty(id):
                # Return the first one that has the property.
                return sheet.getProperty(id)
        # we won't always have PlonePAS groups, due to acquisition,
        # nor are guaranteed property sheets
        # Couldn't find the property in the property sheets. Try to
        # delegate back to the base implementation.

        tool = self.getTool()
        base = aq_base(self)

        # Then, check the user object, the tool, and attrs of myself for a
        # value:
        user_value = getattr(aq_base(self.getGroup()), id, _marker)
        tool_value = tool.getProperty(id, _marker)
        value = getattr(base, id, _marker)

        # Take the first of the above that is filled out:
        for v in [user_value, tool_value, value]:
            if v is not _marker:
                return v

        return default

    def __str__(self):
        return self.getGroupId()

    @security.public
    def isGroup(self):
        """
        isGroup(self,) => Return true if this is a group.
        Will always return true for groups.
        As MemberData objects do not support this method, it is quite useless
        by now.
        So one can use groupstool.isGroup(g) instead to get this information.
        """
        return 1

    # Group object interface ###

    @security.public
    def getGroupName(self):
        return self.getName()

    @security.public
    def getGroupId(self):
        """Get the ID of the group. The ID can be used, at least from
        Python, to get the user from the user's UserDatabase.
        Within Plone, all group ids are UNPREFIXED."""
        return self.getGroup().getId()

    def getGroupTitleOrName(self):
        """Get the Title property of the group. If there is none
        then return the name"""
        title = self.getProperty("title", None)
        return title or self.getGroupName()

    @security.public
    def getMemberId(self):
        """This exists only for a basic user/group API compatibility"""
        return self.getGroupId()

    @security.public
    def getRoles(self):
        """Return the list of roles assigned to a user."""
        return self.getGroup().getRoles()

    @security.public
    def getRolesInContext(self, object):
        """Return the list of roles assigned to the user,  including local
        roles assigned in context of the passed in object."""
        return self.getGroup().getRolesInContext(object)

    @security.public
    def getDomains(self):
        """Return the list of domain restrictions for a user"""
        return self.getGroup().getDomains()

    @security.public
    def has_role(self, roles, object=None):
        """Check to see if a user has a given role or roles."""
        return self.getGroup().has_role(roles, object)

    # GRUF 3.2 methods...

    def getUserName(self):
        return self.getName()

    getUserNameWithoutGroupPrefix = getUserName

    # IManageCapabilities methods
    def canDelete(self):
        """True iff user can be removed from the Plone UI."""
        # IGroupManagement provides removeGroup
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        if managers:
            for mid, manager in managers:
                if IDeleteCapability.providedBy(
                    manager
                ) and manager.allowDeletePrincipal(self.getId()):
                    return True
        return False

    def canPasswordSet(self):
        """Always false for groups, which have no password."""
        return False

    def passwordInClear(self):
        """True iff password can be retrieved in the clear (not hashed.)

        False for PAS. It provides no API for getting passwords,
        though it would be possible to add one in the future.
        """
        return False

    def _groupdataHasProperty(self, prop_name):
        gdata = getToolByName(self, "portal_groupdata", None)
        if gdata:
            return gdata.hasProperty(prop_name)
        return 0

    def canWriteProperty(self, prop_name):
        """True iff the group property named in 'prop_name'
        can be changed.
        """
        # this looks almost exactly like in memberdata. refactor?
        if not IPluggableAuthService.providedBy(self.acl_users):
            # not PAS; Groupdata is writable
            return self._groupdataHasProperty(prop_name)
        else:
            # it's PAS
            group = self.getGroup()
            sheets = getattr(group, "getOrderedPropertySheets", lambda: [])()
            for sheet in sheets:
                if not sheet.hasProperty(prop_name):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    return 1
                else:
                    break  # shadowed by read-only
        return 0

    canAddToGroup = MemberData.canAddToGroup
    canRemoveFromGroup = MemberData.canRemoveFromGroup
    canAssignRole = MemberData.canAssignRole

    # plugin getters

    @security.private
    def _getPlugins(self):
        return self.acl_users.plugins


InitializeClass(GroupData)
