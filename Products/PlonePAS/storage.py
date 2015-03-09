# -*- coding: utf-8 -*-
"""
an archetypes storage that delegates to a pas property provider.

main use.. cmfmember integration w/ properties providers

"""
from AccessControl import ClassSecurityInfo
from Products.Archetypes.public import IStorage
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from zope.interface import implementer


@implementer(IStorage)
class PASStorage(object):

    security = ClassSecurityInfo()

    def get(self, name, instance, **kwargs):
        user = instance.getUser()
        sheets = user.getOrderedSheets()
        for sheet in sheets:
            if sheet.hasProperty(name):
                return sheet.getProperty(name)
        raise AttributeError(name)

    def set(self, name, instance, value, **kwargs):
        user = instance.getUser()
        sheets = user.getOrderedSheets()
        for sheet in sheets:
            if sheet.hasProperty(name):
                if IMutablePropertySheet.providedBy(sheet):
                    sheet.setProperty(name, value)
                else:
                    raise RuntimeError("mutable property provider shadowed by"
                                       "read only provider")
