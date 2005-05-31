"""
$Id: groupdata.py,v 1.9 2005/05/31 23:51:40 jccooper Exp $
"""
from Globals import InitializeClass
from Acquisition import aq_base

from Products.CMFPlone.GroupDataTool import GroupDataTool as BaseGroupDataTool
from Products.GroupUserFolder.GroupDataTool import GroupData as BaseGroupData

from Products.PluggableAuthService.interfaces.authservice \
     import IPluggableAuthService

try:
    from Products.CMFCore.MemberDataTool import CleanupTemp
    _have_cleanup_temp = 1
except:
    _have_cleanup_temp = None

from Products.PluggableAuthService.interfaces.authservice \
     import IPluggableAuthService
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet


class GroupDataTool(BaseGroupDataTool):
    """PAS-specific implementation of groupdata tool. Uses Plone
    GroupDataTool as a base.
    """

    meta_type = "PlonePAS GroupData Tool"

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


class GroupData(BaseGroupData):

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

        if not IPluggableAuthService.isImplementedBy(self.acl_users):
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
                if IMutablePropertySheet.isImplementedBy(sheet):
                    sheet.setProperty(k, v)
                    modified = True
                else:
                    raise RuntimeError, ("Mutable property provider "
                                         "shadowed by read only provider")
        if modified:
            self.notifyModified()

    def getProperty(self, id, default=None):
        """PAS-specific method to fetch a group's properties. Looks
        through the ordered property sheets.
        """
        sheets = None
        if not IPluggableAuthService.isImplementedBy(self.acl_users):
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
        return BaseGroupData.getProperty(self, id)

    def getUserName(self):
        return self.getName()
    getUserNameWithoutGroupPrefix = getUserName

InitializeClass(GroupData)
