"""
Add Mutable Property Sheets and Schema Mutable Property Sheets to PAS

also a property schema type registry which is extensible.

"""

from types import StringTypes, IntType
from types import LongType, FloatType, InstanceType

from zope.component import getUtility
from zope.interface import implements

from DateTime.DateTime import DateTime
from Products.CMFCore.interfaces import ISiteRoot

from Products.PluggableAuthService.UserPropertySheet import _SequenceTypes
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet

class PropertyValueError(ValueError): pass

class PropertySchemaTypeMap(object):

    def __init__(self):
        self.tmap = {}
        self.tmap_order = []

    def addType(self, type_name, identifier, order=None):
        self.tmap[type_name] = identifier
        if order is not None and isinstance(order, int):
            self.tmap_order.insert(order, type_name)
        else:
            self.tmap_order.append(type_name)

    def getTypeFor(self, value):
        ptypes = [(ptype, self.tmap[ptype]) for ptype in self.tmap_order]
        for ptype, inspector in ptypes:
            if inspector(value):
                return ptype
        raise TypeError, 'Invalid property type: %s' % type(value)

    def validate(self, property_type, value):
        inspector = self.tmap[property_type]
        return inspector(value)

PropertySchema = PropertySchemaTypeMap()
PropertySchema.addType('string', lambda x: x is None or type(x) in StringTypes)
PropertySchema.addType('text', lambda x: x is None or type(x) in StringTypes)
PropertySchema.addType('boolean', lambda x: 1)  # anything can be boolean
PropertySchema.addType('int', lambda x:  x is None or type(x) is IntType)
PropertySchema.addType('long', lambda x:  x is None or type(x) is LongType)
PropertySchema.addType('float', lambda x:  x is None or type(x) is FloatType)
PropertySchema.addType('lines', lambda x:  x is None or type(x) in _SequenceTypes)
PropertySchema.addType('selection', lambda x:  x is None or type(x) in StringTypes)
PropertySchema.addType('multiple selection', lambda x:  x is None or type(x) in _SequenceTypes)
PropertySchema.addType('date', lambda x: 1 or x is None or type(x) is InstanceType and isinstance(x, DateTime))
validateValue = PropertySchema.validate

class MutablePropertySheet(UserPropertySheet):

    implements(IMutablePropertySheet)

    def validateProperty(self, id, value):
        if not self._properties.has_key(id):
            raise PropertyValueError, 'No such property found on this schema'

        proptype = self.getPropertyType(id)
        if not validateValue(proptype, value):
            raise PropertyValueError, ("Invalid value (%s) for "
                                       "property '%s' of type %s" %
                                       (value, id, proptype))

    def setProperty(self, user, id, value):
        self.validateProperty(id, value)

        self._properties[id] = value
        self._properties = self._properties

        # cascade to plugin
        provider = self._getPropertyProviderForUser(user)
        provider.setPropertiesForUser(user, self)

    def setProperties(self, user, mapping):
        prop_keys = self._properties.keys()
        prop_update = mapping.copy()

        for key, value in tuple(prop_update.items()):
            if key not in prop_keys:
                prop_update.pop(key)
                continue
            self.validateProperty(key, value)

        self._properties.update(prop_update)

        # cascade to plugin
        provider = self._getPropertyProviderForUser(user)
        provider.setPropertiesForUser(user, self)

    def _getPropertyProviderForUser(self, user):
        # XXX This assumes that the acl_users that we want is in the portal
        # root. This may not always be the case.
        portal = getUtility(ISiteRoot)
        return portal.acl_users._getOb(self._id)


class SchemaMutablePropertySheet(MutablePropertySheet):
    pass

