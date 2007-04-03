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
an archetypes storage that delegates to a pas property provider.

main use.. cmfmember integration w/ properties providers

$Id: storage.py 35196 2006-12-29 21:50:54Z wichert $
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.Archetypes.public import setSecurity, registerStorage, IStorage
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.plugins import IPropertiesProvider
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet

class PASStorage(object):

    security = ClassSecurityInfo()

    def get(self, name, instance, **kwargs):
        user = instance.getUser()
        sheets = user.getOrderedSheets()
        for sheet in sheets:
            if sheet.hasProperty( name ):
                return sheet.getProperty( name )
        raise AttributeError( name )

    def set(self, name, instance, value, **kwargs):
        user = instance.getUser()
        sheets = user.getOrderedSheets()
        for sheet in sheets:
            if sheet.hasProperty( name ):
                if IMutablePropertySheet.providedBy( sheet ):
                    sheet.setProperty( k, v )
                else:
                    raise RuntimeError("mutable property provider shadowed by read only provider")

classImplements(PASStorage,
                IStorage)
