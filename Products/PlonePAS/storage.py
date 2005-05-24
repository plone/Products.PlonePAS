"""
an archetypes storage that delegates to a pas property provider.

main use.. cmfmember integration w/ properties providers

$Id: storage.py,v 1.2 2005/05/24 17:50:00 dreamcatcher Exp $
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.Archetypes.public import setSecurity, registerStorage, IStorage
from Products.PluggableAuthService.interfaces.plugins import IPropertiesProvider
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet

class PASStorage( object ):

    __implements__ = ( IStorage, )

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
                if IMutablePropertySheet.isImplementedBy( sheet ):
                    sheet.setProperty( k, v )
                else:
                    raise RuntimeError("mutable property provider shadowed by read only provider")
