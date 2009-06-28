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
"""
from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized

from zope.interface import implements
from zope.interface import implementedBy

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFPlone.GroupDataTool import GroupDataTool as BaseGroupDataTool
from Products.GroupUserFolder.GroupDataTool import GroupData as BaseGroupData
from Products.GroupUserFolder.GroupDataTool import _marker

from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.authservice \
        import IPluggableAuthService
from Products.PluggableAuthService.PluggableAuthService \
        import _SWALLOWABLE_PLUGIN_EXCEPTIONS

from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.group import IGroupDataTool
from Products.PlonePAS.interfaces.capabilities import IManageCapabilities
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PlonePAS.tools.memberdata import MemberData
from AccessControl.requestmethod import postonly

import logging

logger = logging.getLogger('Plone')

try:
    from Products.CMFCore.MemberDataTool import CleanupTemp
    _have_cleanup_temp = 1
except:
    _have_cleanup_temp = None


class GroupDataTool(BaseGroupDataTool):
    """PAS-specific implementation of groupdata tool. Uses Plone
    GroupDataTool as a base.
    """

    meta_type = "PlonePAS GroupData Tool"
    toolicon = 'tool.gif'
    implements(IGroupDataTool)

    #### an exact copy from the base, so that we pick up the new GroupData.
    #### wrapGroup should have a GroupData factory method to over-ride (or even
    #### set at run-time!) so that we don't have to do this.
    def wrapGroup(self, g):
        """Returns an object implementing the GroupData interface."""

        id = g.getId()
        members = self._members
        if not members.has_key(id):
            # Get a temporary member that might be
            # registered later via registerMemberData().
            temps = self._v_temps
            if temps is not None and temps.has_key(id):
                portal_group = temps[id]
            else:
                base = aq_base(self)
                portal_group = GroupData(base, id)
                if temps is None:
                    self._v_temps = {id:portal_group}
                    if hasattr(self, 'REQUEST'):
                        # No REQUEST during tests.
                        # XXX jcc => CleanupTemp doesn't seem to work
                        # on Plone 1.0.3.  Have to find a way to pass
                        # around...
                        if _have_cleanup_temp:
                            self.REQUEST._hold(CleanupTemp(self))
                else:
                    temps[id] = portal_group
        else:
            portal_group = members[id]
        # Return a wrapper with self as containment and
        # the user as context.
        return portal_group.__of__(self).__of__(g)

InitializeClass(GroupDataTool)
registerToolInterface('portal_groupdata', IGroupDataTool)


class GroupData(BaseGroupData):

    security = ClassSecurityInfo()

    def _getGroup(self):
        """Get the underlying group object in a PAS-acceptable way.
        (I don't even know why there's the two different ways for GRUF. Speed?)
        """
        return self.getGroup()

    ## setProperties uses setGroupProperties. no need to override.
    def setGroupProperties(self, mapping):
        """PAS-specific method to set the properties of a group.
        """
        sheets = None

        if not IPluggableAuthService.providedBy(self.acl_users):
            # Defer to base impl in absence of PAS, a PAS group, or
            # property sheets
            return BaseGroupData.setGroupProperties(self, mapping)
        else:
            # It's a PAS! Whee!
            group = self.getGroup()
            sheets = getattr(group, 'getOrderedPropertySheets', lambda: None)()

            # We won't always have PlonePAS groups, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                # Defer to base impl if we have a PAS but no property
                # sheets.
                return BaseGroupData.setGroupProperties(self, mapping)

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
                    raise RuntimeError, ("Mutable property provider "
                                         "shadowed by read only provider")
        if modified:
            self.notifyModified()

    def getProperty(self, id, default=_marker):
        """PAS-specific method to fetch a group's properties. Looks
        through the ordered property sheets.
        """
        sheets = None
        if not IPluggableAuthService.providedBy(self.acl_users):
            return BaseGroupData.getProperty(self, id)
        else:
            # It's a PAS! Whee!
            group = self.getGroup()
            sheets = getattr(group, 'getOrderedPropertySheets', lambda: None)()
            # we won't always have PlonePAS groups, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                return BaseGroupData.getProperty(self, id)

        # If we made this far, we found a PAS and some property sheets.
        for sheet in sheets:
            if sheet.hasProperty(id):
                # Return the first one that has the property.
                return sheet.getProperty(id)
        # Couldn't find the property in the property sheets. Try to
        # delegate back to the base implementation.
        return BaseGroupData.getProperty(self, id, default)

    def getUserName(self):
        return self.getName()
    getUserNameWithoutGroupPrefix = getUserName

    def getGroupName(self):
        return self.getName()

    ## GRUF 3.2 methods...

    def _getGRUF(self,):
        return self.acl_users

    @postonly
    def addMember(self, id, REQUEST=None):
        """ Add the existing member with the given id to the group"""
        if not self.canAdministrateGroup():
            raise Unauthorized, "You cannot add a member to the group."
        
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            try:
                if manager.addPrincipalToGroup(id, self.getId()):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                pass

    @postonly
    def removeMember(self, id, REQUEST=None):
        """Remove the member with the provided id from the group.
        """
        if not self.canAdministrateGroup():
            raise Unauthorized, "You cannot remove a member from the group."

        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            try:
                if manager.removePrincipalFromGroup(id, self.getId()):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                pass


    def getAllGroupMembers(self, ):
        """
        Returns a list of the portal_memberdata-ish members of the group.
        This will include transitive groups / users
        """
        md = self.portal_memberdata
        gd = self.portal_groupdata
        ret = []
        for u_name in self.getGroup().getMemberIds():
            usr = self._getGRUF().getUserById(u_name)
            if not usr:
                usr = self._getGRUF().getGroupById(u_name)
                if not usr:
                    logger.debug("Group has a non-existing principal %s" % u_name)
                    continue
                ret.append(usr)
            else:
                ret.append(md.wrapUser(usr))
        return ret

    def getGroupMembers(self):
        """
        Returns a list of the portal_memberdata-ish members of the group.
        This doesn't include TRANSITIVE groups/users.
        """
        md = self.portal_memberdata
        gd = self.portal_groupdata
        gtool = self.portal_groups
        ret = []
        for u_name in gtool.getGroupMembers(self.getId()):
            usr = self._getGRUF().getUserById(u_name)
            # getUserById from Products.PluggableAuthService.PluggableAuthService
            # The returned object is not wrapped, we wrapped it below
            if not usr:
                usr = self._getGRUF().getGroupById(u_name)
                # getGroupById from Products.PlonePAS.pas
                # The returned object is already wrapped
                if not usr:
                    logger.debug("Group has a non-existing principal %s" % u_name)
                    continue
                ret.append(usr)
            else:
                ret.append(md.wrapUser(usr))
        return ret

    def setProperties(self, properties=None, **kw):
        """Allows the manager group to set his/her own properties.
        Accepts either keyword arguments or a mapping for the "properties"
        argument.
        """
        if properties is None:
            properties = kw
        return self.setGroupProperties(properties)

    def getProperties(self):
        """ Return the properties of this group. Properties are as usual in Zope.
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

    ## IManageCapabilities methods
    def canDelete(self):
        """True iff user can be removed from the Plone UI.
        """
        # IGroupManagement provides removeGroup
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        if managers:
            for mid, manager in managers:
                if (IDeleteCapability.providedBy(manager) and
                        manager.allowDeletePrincipal(self.getId())):
                    return True
        return False

    def canPasswordSet(self):
        """Always false for groups, which have no password.
        """
        return False

    def passwordInClear(self):
        """True iff password can be retrieved in the clear (not hashed.)

        False for PAS. It provides no API for getting passwords,
        though it would be possible to add one in the future.
        """
        return False

    def _groupdataHasProperty(self, prop_name):
        gdata = getToolByName(self, 'portal_groupdata', None)
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
            sheets = getattr(group, 'getOrderedPropertySheets', lambda: None)()
            if not sheets:
                return self._groupdataHasProperty(prop_name)

            for sheet in sheets:
                if not sheet.hasProperty(prop_name):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    return 1
                else:
                    break  # shadowed by read-only
        return 0

    canAddToGroup = MemberData.canAddToGroup.im_func
    canRemoveFromGroup = MemberData.canRemoveFromGroup.im_func
    canAssignRole = MemberData.canAssignRole.im_func

    ## plugin getters

    security.declarePrivate('_getPlugins')
    def _getPlugins(self):
        return self.acl_users.plugins

classImplements(GroupData,
                implementedBy(BaseGroupData),
                IManageCapabilities)

InitializeClass(GroupData)
