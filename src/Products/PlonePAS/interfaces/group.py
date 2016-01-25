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
    "Import from Products.CMFPlone.interfaces.pas instead",
    IGrouptool="Products.CMFPlone.interfaces.pas:IGroupTool",
)

deprecated(
    "Import from Products.PluggableAuthService.interfaces.group instead",
    IGroupData="Products.PluggableAuthService.interfaces.group:"
               "IGroupData",
)


class IGroupDataTool(Interface):

    def wrapGroup(group):
        """
        decorate a group with property management capabilities if needed
        """

