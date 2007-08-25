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

from zope.interface import implementedBy

from Products.CMFPlone.MemberDataTool import MemberDataTool as BaseMemberDataTool

from Products.CMFCore.MemberDataTool import MemberData as BaseMemberData


from Products.CMFCore.utils import getToolByName
from Products.CMFCore.MemberDataTool import CleanupTemp
from Products.CMFPlone.MemberDataTool import _marker

from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin, IRoleAssignerPlugin

from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability, IPasswordSetCapability
from Products.PlonePAS.interfaces.capabilities import IGroupCapability, IAssignRoleCapability
from Products.PlonePAS.interfaces.capabilities import IManageCapabilities
from Products.PlonePAS.utils import getCharset
from AccessControl.requestmethod import postonly


class MemberDataTool(BaseMemberDataTool):
    """PAS-specific implementation of memberdata tool. Uses Plone
    MemberDataTool as a base.
    """

    meta_type = "PlonePAS MemberData Tool"
    toolicon = 'tool.gif'

    #### an exact copy from the base, so that we pick up the new MemberData.
    #### wrapUser should have a MemberData factory method to over-ride (or even
    #### set at run-time!) so that we don't have to do this.
    def wrapUser(self, u):
        '''
        If possible, returns the Member object that corresponds
        to the given User object.
        We override this to ensure OUR MemberData class is used
        '''
        id = u.getId()
        members = self._members
        if not members.has_key(id):
            base = aq_base(self)
            members[id] = MemberData(base, id)
        # Return a wrapper with self as containment and
        # the user as context.
        return members[id].__of__(self).__of__(u)

    @postonly
    def deleteMemberData(self, member_id, REQUEST=None):
        """ Delete member data of specified member.
        """
        if IPluggableAuthService.providedBy(self.acl_users):
            # It's a PAS! Whee!
            # XXX: can we safely assume that user name == member_id
            plugins = self._getPlugins()
            prop_managers = plugins.listPlugins(IPropertiesPlugin)
            for mid, prop_manager in prop_managers:
                # Not all PropertiesPlugins support user deletion
                try:
                    prop_manager.deleteUser(member_id)
                except AttributeError:
                    pass

        # we won't always have PlonePAS users, due to acquisition,
        # nor are guaranteed property sheets
        members = self._members
        if members.has_key(member_id):
            del members[member_id]
            return 1
        else:
            return 0

    ## plugin getter
    def _getPlugins(self):
        return self.acl_users.plugins

InitializeClass(MemberDataTool)


class MemberData(BaseMemberData):

    security = ClassSecurityInfo()

    ## setProperties uses setMemberProperties. no need to override.

    def setMemberProperties(self, mapping, force_local = 0):
        """PAS-specific method to set the properties of a
        member. Ignores 'force_local', which is not reliably present.
        """
        sheets = None

        # We could pay attention to force_local here...
        if not IPluggableAuthService.providedBy(self.acl_users):
            # Defer to base impl in absence of PAS, a PAS user, or
            # property sheets
            return BaseMemberData.setMemberProperties(self, mapping)
        else:
            # It's a PAS! Whee!
            user = self.getUser()
            sheets = getattr(user, 'getOrderedPropertySheets', lambda: None)()

            # We won't always have PlonePAS users, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                # Defer to base impl if we have a PAS but no property
                # sheets.
                return BaseMemberData.setMemberProperties(self, mapping)

        # If we got this far, we have a PAS and some property sheets.
        # XXX track values set to defer to default impl
        # property routing?
        modified = False
        for k, v in mapping.items():
            for sheet in sheets:
                if not sheet.hasProperty(k):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    sheet.setProperty(user, k, v)
                    modified = True
                else:
                    break
                    #raise RuntimeError, ("Mutable property provider "
                    #                     "shadowed by read only provider")
        if modified:
            self.notifyModified()

    def getProperty(self, id, default=_marker):
        """PAS-specific method to fetch a user's properties. Looks
        through the ordered property sheets.
        """
        sheets = None
        if not IPluggableAuthService.providedBy(self.acl_users):
            return BaseMemberData.getProperty(self, id)
        else:
            # It's a PAS! Whee!
            user = self.getUser()
            sheets = getattr(user, 'getOrderedPropertySheets', lambda: None)()

            # we won't always have PlonePAS users, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                return BaseMemberData.getProperty(self, id, default)

        charset = getCharset(self)

        # If we made this far, we found a PAS and some property sheets.
        for sheet in sheets:
            if sheet.hasProperty(id):
                # Return the first one that has the property.
                value = sheet.getProperty(id)
                if isinstance(value, unicode):
                    # XXX Temporarily work around the fact that
                    # property sheets blindly store and return
                    # unicode. This is sub-optimal and should be
                    # dealed with at the property sheets level by
                    # using Zope's converters.
                    return value.encode(charset)
                return value

        # Couldn't find the property in the property sheets. Try to
        # delegate back to the base implementation.
        return BaseMemberData.getProperty(self, id, default)

    def getPassword(self):
        """Returns None. Present to avoid NotImplementedError."""
        return None

    ## IManageCapabilities methods

    def canDelete(self):
        """True iff user can be removed from the Plone UI."""
        # IUserManagement provides doDeleteUser
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IUserManagement)
        for mid, manager in managers:
            if (IDeleteCapability.providedBy(manager) and
                    manager.allowDeletePrincipal(self.getId())):
                return True
        return False

    def canPasswordSet(self):
        """True iff user can change password."""
        # IUserManagement provides doChangeUser
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IUserManagement)
        for mid, manager in managers:
            if (IPasswordSetCapability.providedBy(manager) and
                    manager.allowPasswordSet(self.getId())):
                return True
        return False

    def passwordInClear(self):
        """True iff password can be retrieved in the clear (not hashed.)

        False for PAS. It provides no API for getting passwords,
        though it would be possible to add one in the future.
        """
        return 0

    def _memberdataHasProperty(self, prop_name):
        mdata = getToolByName(self, 'portal_memberdata', None)
        if mdata:
            return mdata.hasProperty(prop_name)
        return 0

    def canWriteProperty(self, prop_name):
        """True iff the member/group property named in 'prop_name'
        can be changed.
        """
        if not IPluggableAuthService.providedBy(self.acl_users):
            # not PAS; Memberdata is writable
            return self._memberdataHasProperty(prop_name)
        else:
            # it's PAS
            user = self.getUser()
            sheets = getattr(user, 'getOrderedPropertySheets', lambda: None)()
            if not sheets:
                return self._memberdataHasProperty(prop_name)

            for sheet in sheets:
                if not sheet.hasProperty(prop_name):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    # BBB for plugins implementing an older version of IMutablePropertySheet
                    if hasattr(sheet, 'canWriteProperty'):
                        return sheet.canWriteProperty(user, prop_name)
                    return True
                else:
                    break  # shadowed by read-only
        return False

    def canAddToGroup(self, group_id):
        """True iff member can be added to group."""
        # IGroupManagement provides IGroupCapability
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            if (IGroupCapability.providedBy(manager) and
                    manager.allowGroupAdd(self.getId(), group_id)):
                return True
        return False

    def canRemoveFromGroup(self, group_id):
        """True iff member can be removed from group."""
        # IGroupManagement provides IGroupCapability
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            if (IGroupCapability.providedBy(manager) and
                    manager.allowGroupRemove(self.getId(), group_id)):
                return True
        return False


    def canAssignRole(self, role_id):
        """True iff member can be assigned role. Role id is string."""
        # IRoleAssignerPlugin provides IAssignRoleCapability
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IRoleAssignerPlugin)
        for mid, manager in managers:
            if (IAssignRoleCapability.providedBy(manager) and
                    manager.allowRoleAssign(self.getId(), role_id)):
                return True
        return False

    ## plugin getters

    security.declarePrivate('_getPlugins')
    def _getPlugins(self):
        return self.acl_users.plugins

classImplements(MemberData,
                implementedBy(BaseMemberData),
                IManageCapabilities)

InitializeClass(MemberData)
