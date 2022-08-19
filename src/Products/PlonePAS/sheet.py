"""
Add Mutable Property Sheets and Schema Mutable Property Sheets to PAS

also a property schema type registry which is extensible.

"""
from Products.CMFCore.interfaces import ISiteRoot
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from zope.component import getUtility
from zope.interface import implementer


class PropertyValueError(ValueError):
    pass


class PropertySchemaTypeMap:
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
        raise TypeError("Invalid property type: %s" % type(value))

    def validate(self, property_type, value):
        inspector = self.tmap[property_type]
        return inspector(value)


PropertySchema = PropertySchemaTypeMap()
PropertySchema.addType("string", lambda x: x is None or isinstance(x, str))
PropertySchema.addType("text", lambda x: x is None or isinstance(x, str))
PropertySchema.addType("boolean", lambda x: 1)  # anything can be boolean
PropertySchema.addType("int", lambda x: x is None or isinstance(x, int))
PropertySchema.addType("long", lambda x: x is None or isinstance(x, int))  # theres is no long in Python 3
PropertySchema.addType("float", lambda x: x is None or isinstance(x, float))
PropertySchema.addType("lines", lambda x: x is None or isinstance(x, (tuple, list)))
PropertySchema.addType("selection", lambda x: x is None or isinstance(x, str))
PropertySchema.addType(
    "multiple selection", lambda x: x is None or isinstance(x, (tuple, list))
)
PropertySchema.addType("date", lambda x: 1)
validateValue = PropertySchema.validate


@implementer(IMutablePropertySheet)
class MutablePropertySheet(UserPropertySheet):
    def validateProperty(self, id, value):
        if id not in self._properties:
            raise PropertyValueError("No such property found on this schema")

        proptype = self.getPropertyType(id)
        if not validateValue(proptype, value):
            raise PropertyValueError(
                "Invalid value (%s) for property '%s' of type %s"
                % (value, id, proptype)
            )

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
