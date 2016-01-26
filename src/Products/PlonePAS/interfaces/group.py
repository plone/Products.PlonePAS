# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope.deferredimport import deprecated


class IGroupManagement(Interface):

    def addGroup(id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        return True if the operation suceeded
        """

    def addPrincipalToGroup(principal_id, group_id):
        """
        Add a given principal to the group.
        return True on success
        """

    def updateGroup(id, **kw):
        """
        Edit the given group. plugin specific
        return True on success
        """

    def setRolesForGroup(group_id, roles=()):
        """
        set roles for group
        return True on success
        """

    def removeGroup(group_id):
        """
        Remove the given group
        return True on success
        """

    def removePrincipalFromGroup(principal_id, group_id):
        """
        remove the given principal from the group
        return True on success
        """

deprecated(
    "Import from Products.PluggableAuthService.interfaces.plugins instead",
    IGroupIntrospection="Products.PluggableAuthService.interfaces.plugins:"
                        "IGroupIntrospection",
)

deprecated(
    "Import from Products.CMFPlone.interfaces.groups instead",
    IGroupTool="Products.CMFPlone.interfaces.groups:IGroupTool",
)

deprecated(
    "Import from Products.CMFPlone.interfaces.groups instead",
    IGroupData="Products.CMFPlone.interfaces.groups:IGroupData",
)

deprecated(
    "Import from Products.CMFPlone.interfaces.membership instead",
    IMembershipTool="Products.CMFPlone.interfaces.membership:IMembershipTool",
)

deprecated(
    "Import from Products.CMFPlone.interfaces.groups instead",
    IGroupDataTool="Products.CMFPlone.interfaces.groups:IGroupDataTool",
)
