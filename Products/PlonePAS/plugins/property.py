##############################################################################
#
# Copyright (c) 2005 Kapil Thangavelu
# Reserved.
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
Mutable Property Provider
$Id: property.py,v 1.5 2005/05/24 17:50:11 dreamcatcher Exp $
"""
from sets import Set

from ZODB.PersistentMapping import PersistentMapping
from BTrees.OOBTree import OOBTree
from Globals import DTMLFile

from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.UserPropertySheet import _guessSchema
from Products.PlonePAS.sheet import MutablePropertySheet, validateValue
from Products.PlonePAS.interfaces.plugins import IMutablePropertiesPlugin


def manage_addZODBMutablePropertyProvider(self, id, title='', RESPONSE=None, schema=None, **kw):
    """
    Create an instance of a mutable property manager.
    """
    o = ZODBMutablePropertyProvider(id, title, schema, **kw)
    self._setObject(o.getId(), o)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addZODBMutablePropertyProviderForm = DTMLFile("../zmi/MutablePropertyProviderForm", globals())

class ZODBMutablePropertyProvider(BasePlugin):

    meta_type = 'ZODB Mutable Property Provider'
    __implements__ = ( IPropertiesPlugin, IMutablePropertiesPlugin, )

    def __init__(self, id, title='', schema=None, **kw):
        """ Create in-ZODB mutable property provider.
        Provide a schema either as a list of (name,type,value) tuples in the 'schema' parameter
        or as a series of keyword parameters 'name=value'. Types will be guessed in this case.
        The 'value' is meant as the default value, and will be used unless the user provides data.

        If no schema is provided by constructor, the properties of the portal_memberdata object will
        be used.

        Types available: string, boolean, int, long, float, lines, date
        """
        self.id = id
        self.title = title
        self._storage = OOBTree()

        # calculate schema and default values
        defaultvalues = {}
        if schema is None:
            schema = _guessSchema(kw)
            defaultvalues = kw
        else:
            schema = [(name, type) for name, type, value in schema]
            valuetuples = [(name, value) for name, type, value in schema]
            for name, value in valuetuples: defaultvalues[name] = value
        self._schema = tuple(schema)
        self._defaultvalues = defaultvalues

        # don't use _schema directly or you'll lose the fallback! use _getSchema instead
        # same for default values

    def _getSchema(self):
        schema = self._schema
        if not schema:       # if no schema is provided, use portal_memberdata properties
            schema = ()
            mdtool = getToolByName(self, 'portal_memberdata')
            mdschema = mdtool.propertyMap()
            schema = [(elt['id'], elt['type']) for elt in mdschema]
        return schema

    def _getDefaultValues(self):
        defaultvalues = self._defaultvalues
        if not self._schema:          # if no schema is provided, use portal_memberdata properties
            defaultvalues = {}
            mdtool = getToolByName(self, 'portal_memberdata')
            mdvalues = mdtool.propertyItems()   # we rely on propertyMap and propertyItems mapping
            for name, value in mdvalues: defaultvalues[name] = value
        return defaultvalues

    def getPropertiesForUser(self, user, request=None):
        """Get property values for a user. Returns a dictionary of values or a PropertySheet.
        This implementation will always return a MutablePropertySheet.

        NOTE: Must always return something, or else the property sheet won't
        get created and this will screw up portal_memberdata.
        """
        data = self._storage.get(user.getId())
        if data is None:
            data = self._getDefaultValues()
        return MutablePropertySheet(self.id, user, schema=self._getSchema(), **data)

    def setPropertiesForUser(self, user, propertysheet):
        properties = dict( propertysheet.propertyItems() )

        for property_type, name in self._getSchema() or ():
            if name in properties and not validateValue( property_type, properties[ name ] ):
                raise ValueError("Invalid Value %s does not conform to %s"%( name, property_type) )

        allowed_prop_keys = [ pt for pt, pn in self._getSchema() or () ]
        if allowed_prop_keys:
            prop_names = Set( properties.keys() ) - Set( allowed_prop_keys )
            if prop_names:
                raise ValueError("Unknown Properties")

        userprops = self._storage.get(user.getId())
        if userprops is not None:
            userprops.update(properties)
        else:
            self._storage.insert(user.getId(), properties)

class PersistentProperties( PersistentMapping ): pass
