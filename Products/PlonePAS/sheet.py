"""
Add Mutable Property Sheets and Schema Mutable Property Sheets to PAS

also a property schema type registry which is extensible.

$Id: sheet.py,v 1.6 2005/05/07 01:27:48 jccooper Exp $
"""

from types import StringTypes, BooleanType, IntType, LongType, FloatType, InstanceType
from DateTime.DateTime import DateTime
from Products.PluggableAuthService.UserPropertySheet import _SequenceTypes

from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet

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
        for ptype, inspector in [ (ptype, self.tmap[ptype]) for ptype in self.tmap_order ]:
            if inspector(value):
                return ptype
        raise TypeError("invalid property type %s"%(type(value)))

    def validate(self, property_type, value):
        inspector = self.tmap[property_type]
        return inspector(value)

PropertySchema = PropertySchemaTypeMap()
PropertySchema.addType('string', lambda x: x is None or type(x) in StringTypes)
PropertySchema.addType('boolean', lambda x: 1)  # anything can be boolean
PropertySchema.addType('int', lambda x:  x is None or type(x) is IntType)
PropertySchema.addType('long', lambda x:  x is None or type(x) is LongType)
PropertySchema.addType('float', lambda x:  x is None or type(x) is FloatType)
PropertySchema.addType('lines', lambda x:  x is None or type(x) in _SequenceTypes)
PropertySchema.addType('date', lambda x: 1 or x is None or type(x) is InstanceType and isinstance(x, DateTime))
validateValue = PropertySchema.validate


class MutablePropertySheet(UserPropertySheet):

    __implements__ = (IMutablePropertySheet,)

    def __init__(self, id, user, **kw ):
        UserPropertySheet.__init__(self, id, **kw)
        self._user = user   # have to have a handle on container, since we're not acquisition-aware

    def validateProperty(self, id, value):
        if not self._properties.has_key(id): 
            raise PropertyValueError("no such property found on this schema")

        proptype = self.getPropertyType(id)
        if not validateValue(proptype, value):
            raise PropertyValueError("invalid value (%s) for property '%s' of type %s" % (value,id, proptype))
        
    def setProperty(self, id, value):
        self.validateProperty(id, value)
        
        self._properties[id] = value
        
        # cascade to plugin
        provider = self.getPropertyProvider()
        user = self.getPropertiedUser()
        provider.setPropertiesForUser(user, self)
        
    def setProperties(self, mapping):
        prop_keys = self._properties.keys()
        prop_update = mapping.copy()
        
        for key, value in tuple(prop_update.items()):
            if key not in prop_keys:
                prop_update.pop( key )
                continue
            self.validateProperty(key, value)

        self._properties.update(prop_update)
        
        # cascade to plugin
        provider = self.getPropertyProvider()
        user = self.getPropertiedUser()
        provider.setPropertiesForUser(user, self)

    def getPropertiedUser(self):
        return self._user

    def getPropertyProvider(self, context=None):
        context = context or self._user
        return context.acl_users._getOb(self._id)
    
class SchemaMutablePropertySheet(MutablePropertySheet):

    __implements__ = ( IMutablePropertySheet, )



    
