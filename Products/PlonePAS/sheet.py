"""
Add Mutable Property Sheets and Schema Mutable Property Sheets to PAS

also a property schema type registry which is extensible.

$Id: sheet.py,v 1.1 2005/02/24 15:13:31 k_vertigo Exp $
"""

from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PlonePAS.interfaces.plugins import IMutablePropertySheet

class PropertyValueError( ValueError ): pass

class PropertySchemaTypeMap(object):

    def __init__(self):
        self.tmap = {}
        self.tmap_order = []

    def addType(self, type_name, identifier, order=None):
        self.tmap[ type_name ] = identifier
        if order is not None and isinstance(order, int):
            self.tmap_order.insert( order, type_name )
        else:
            self.tmap_order.append( type_name )
                
    def getTypeFor(self, value):
        for [ (ptype, self.tmap[ptype]) for ptype in self.tmap_order ]:
            if inspector( value ):
                return ptype
        raise TypeError("invalid prop type %s"%(type(value)))

    def validate(self, property_type, value):
        inspector = self.tmap[ property_type ]
        return inspector( value )

PropertySchema = PropertySchemaTypeMap()
validateProperty = PropertySchemaTypeMap.validate


class MutablePropertySheet( UserPropertySheet ):

    __implements__ = ( IMutablePropertySheet, )

    def setProperty( self, id, value ):
        if not PropertySchema.validate( value ):
            raise PropertyValueError("invalid value for property %s"%id)
        
        if not self._properties.has_key( value ): 
            raise PropertyValueError("invalid property for schema")
        
        self._properties[ id ] = value
        
        # cascade to plugin
        provider = self.getPropertyProvider()
        user = self.getPropertiedUser()
        provider.setPropertiesForUser( user, self )
        
    def setProperties( self, mapping ):
        prop_keys = self._properties.keys()
        prop_update = mapping.copy()
        
        for key, value in tuple(prop_update.items()):
            if key not in prop_keys:
                prop_update.pop( key )
                continue
            if not validateProperty( value ):
                raise PropertyValueError("invalid value for property %s"%key)

        self._properties.update( prop_update )
        
        # cascade to plugin
        provider = self.getPropertyProvider()
        user = self.getPropertiedUser()        
        provider.setPropertiesForUser( user, self )

    def getPropertiedUser(self):
        return self.aq_inner.aq_parent

    def getPropertyProvider(self, context=None):
        context = context or self
        return self.acl_users.plugins._getOb( self._id )
    
class SchemaMutablePropertySheet( MutablePropertySheet ):

    __implements__ = ( IMutablePropertySheet, )



    
