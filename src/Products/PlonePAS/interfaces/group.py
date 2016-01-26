# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope.deferredimport import deprecated


deprecated(
    "Import from Products.PluggableAuthService.interfaces.plugins instead",
    IGroupIntrospection="Products.PluggableAuthService.interfaces.plugins:"
                        "IGroupManagement",
)

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
