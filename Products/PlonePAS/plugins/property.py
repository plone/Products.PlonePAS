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
$Id: property.py,v 1.3 2005/05/04 18:27:18 jccooper Exp $
"""
from sets import Set

from ZODB.PersistentMapping import PersistentMapping
from BTrees.OOBTree import OOBTree
from Globals import DTMLFile

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PlonePAS.sheet import MutablePropertySheet, validateValue
from Products.PlonePAS.interfaces.plugins import IMutablePropertiesPlugin

def manage_addZODBMutablePropertyProvider(self, id, title='', RESPONSE=None):
    """
    Create an instance of a mutable property manager.
    """
    o = ZODBMutablePropertyProvider(id, title)
    self._setObject(o.getId(), o)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addZODBMutablePropertyProviderForm = DTMLFile("../zmi/MutablePropertyProviderForm", globals())

class ZODBMutablePropertyProvider(BasePlugin):

    meta_type = 'ZODB Mutable Property Provider'
    __implements__ = ( IPropertiesPlugin, IMutablePropertiesPlugin, )

    def __init__(self, id, title=''):
        self.id = id
        self.title = title
        self._storage = OOBTree()
        self._schema = None  # define a schema for property requests handled by
                             # this provider, else assume

    def getPropertiesForUser(self, user, request=None):
        data = self._storage.get( user.getId() )
        if data is None:
            return None     # should return something so a property sheet is created
        return self.id, MutablePropertySheet( self.id, self._schema, **data )

    def setPropertiesForUser(self, user, propertysheet):
        properties = dict( propertysheet.propertyItems() )
        
        for property_type, name in self._schema or ():
            if name in properties and not validateValue( property_type, properties[ name ] ):
                raise ValueError("Invalid Value %s does not conform to %s"%( name, property_type) )

        allowed_prop_keys = [ pt for pt, pn in self._schema or () ]
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


