"""
Mutable Property Provider
"""
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from App.special_dtml import DTMLFile
from BTrees.OOBTree import OOBTree
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.plugins import IMutablePropertiesPlugin
from Products.PlonePAS.sheet import MutablePropertySheet
from Products.PlonePAS.sheet import validateValue
from Products.PlonePAS.utils import safe_unicode
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.UserPropertySheet import _guessSchema
from ZODB.PersistentMapping import PersistentMapping
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

import copy


_ = MessageFactory("plone")


def manage_addZODBMutablePropertyProvider(
    self, id, title="", RESPONSE=None, schema=None, **kw
):
    """
    Create an instance of a mutable property manager.
    """
    o = ZODBMutablePropertyProvider(id, title, schema, **kw)
    self._setObject(o.getId(), o)

    if RESPONSE is not None:
        RESPONSE.redirect("manage_workspace")


manage_addZODBMutablePropertyProviderForm = DTMLFile(
    "../zmi/MutablePropertyProviderForm", globals()
)


def isStringType(data):
    return isinstance(data, str) or isinstance(data, str)


@implementer(IPropertiesPlugin, IUserEnumerationPlugin, IMutablePropertiesPlugin)
class ZODBMutablePropertyProvider(BasePlugin):
    """Storage for mutable properties in the ZODB for users/groups.

    API sounds like it's only for users, but groups work as well.
    """

    meta_type = "ZODB Mutable Property Provider"

    security = ClassSecurityInfo()

    def __init__(self, id, title="", schema=None, **kw):
        """Create in-ZODB mutable property provider.

        Provide a schema either as a list of (name,type,value) tuples
        in the 'schema' parameter or as a series of keyword parameters
        'name=value'. Types will be guessed in this case.

        The 'value' is meant as the default value, and will be used
        unless the user provides data.

        If no schema is provided by constructor, the properties of the
        portal_memberdata object will be used.

        Types available: string, text, boolean, int, long, float, lines, date
        """
        self.id = id
        self.title = title
        self._storage = OOBTree()

        # calculate schema and default values
        defaultvalues = {}
        if not schema and not kw:
            schema = ()
        elif not schema and kw:
            schema = _guessSchema(kw)
            defaultvalues = kw
        else:
            valuetuples = [(name, value) for name, type, value in schema]
            schema = [(name, type) for name, type, value in schema]
            for name, value in valuetuples:
                defaultvalues[name] = value
        self._schema = tuple(schema)
        self._defaultvalues = defaultvalues

    def _getSchema(self, isgroup=None):
        # this could probably stand to be cached
        datatool = isgroup and "portal_groupdata" or "portal_memberdata"

        schema = self._schema
        if not schema:
            # if no schema is provided, use portal_memberdata properties
            schema = ()
            mdtool = getToolByName(self, datatool, None)
            # Don't fail badly if tool is not available.
            if mdtool is not None:
                mdschema = mdtool.propertyMap()
                schema = [(elt["id"], elt["type"]) for elt in mdschema]
        return schema

    def _getDefaultValues(self, isgroup=None):
        """Returns a dictionary mapping of property names to default values.
        Defaults to portal_*data tool if necessary.
        """
        datatool = isgroup and "portal_groupdata" or "portal_memberdata"

        defaultvalues = self._defaultvalues
        if not self._schema:
            # if no schema is provided, use portal_*data properties
            defaultvalues = {}
            mdtool = getToolByName(self, datatool, None)
            # Don't fail badly if tool is not available.
            if mdtool is not None:
                # we rely on propertyMap and propertyItems mapping
                mdvalues = mdtool.propertyItems()
                for name, value in mdvalues:
                    # For selection types the default value is the name of a
                    # method which returns the possible values. There is no way
                    # to set a default value for those types.
                    ptype = mdtool.getPropertyType(name)
                    if ptype == "selection":
                        defaultvalues[name] = ""
                    elif ptype == "multiple selection":
                        defaultvalues[name] = []
                    else:
                        defaultvalues[name] = value

            # ALERT! if someone gives their *_data tool a title, and want a
            #        title as a property of the user/group (and groups do by
            #        default) we don't want them all to have this title, since
            #        a title is used in the UI if it exists
            if defaultvalues.get("title"):
                defaultvalues["title"] = ""
        return defaultvalues

    @security.private
    def getPropertiesForUser(self, user, request=None):
        """Get property values for a user or group.
        Returns a dictionary of values or a PropertySheet.

        This implementation will always return a MutablePropertySheet.

        NOTE: Must always return something, or else the property sheet
        won't get created and this will screw up portal_memberdata.
        """
        isGroup = getattr(user, "isGroup", lambda: None)()

        data = self._storage.get(user.getId())
        defaults = self._getDefaultValues(isGroup)

        # provide default values where missing
        if not data:
            data = {}
        for key, val in defaults.items():
            if key not in data:
                data[key] = val

        return MutablePropertySheet(self.id, schema=self._getSchema(isGroup), **data)

    @security.private
    def setPropertiesForUser(self, user, propertysheet):
        """Set the properties of a user or group based on the contents of a
        property sheet.
        """
        isGroup = getattr(user, "isGroup", lambda: None)()

        properties = dict(propertysheet.propertyItems())

        for name, property_type in self._getSchema(isGroup) or ():
            if name in properties and not validateValue(
                property_type, properties[name]
            ):
                raise ValueError(
                    "Invalid value: {} does not conform to {}".format(
                        name, property_type
                    )
                )

        allowed_prop_keys = [pn for pn, pt in self._getSchema(isGroup) or ()]
        if allowed_prop_keys:
            prop_names = set(properties.keys()) - set(allowed_prop_keys)
            if prop_names:
                raise ValueError("Unknown Properties: %r" % prop_names)

        userid = user.getId()
        userprops = self._storage.get(userid)
        properties.update({"isGroup": isGroup})
        if userprops is not None:
            userprops.update(properties)
            # notify persistence machinery of change
            self._storage[userid] = self._storage[userid]
        else:
            self._storage.insert(user.getId(), properties)

    @security.private
    def deleteUser(self, user_id):
        """Delete all user properties"""
        # Do nothing if an unknown user_id is given
        try:
            del self._storage[user_id]
        except KeyError:
            pass

    @security.private
    def testMemberData(self, memberdata, criteria, exact_match=False):
        """Test if a memberdata matches the search criteria."""
        for (key, value) in criteria.items():
            testvalue = memberdata.get(key, None)
            if testvalue is None:
                return False

            if isStringType(testvalue):
                testvalue = safe_unicode(testvalue.lower())
            if isStringType(value):
                value = safe_unicode(value.lower())

            if exact_match:
                if value != testvalue:
                    return False
            else:
                try:
                    if value not in testvalue:
                        return False
                except TypeError:
                    # Fall back to exact match if we can check for
                    # sub-component
                    if value != testvalue:
                        return False

        return True

    @security.private
    def enumerateUsers(self, id=None, login=None, exact_match=False, **kw):
        """See IUserEnumerationPlugin."""
        plugin_id = self.getId()

        # This plugin can't search for a user by id or login, because there is
        # no such keys in the storage (data dict in the comprehensive list)
        # If kw is empty or not, we continue the search.
        if id is not None or login is not None:
            return ()

        criteria = copy.copy(kw)

        users = [
            (user, data)
            for (user, data) in self._storage.items()
            if self.testMemberData(data, criteria, exact_match)
            and not data.get("isGroup", False)
        ]

        user_info = [
            {
                "id": self.prefix + user_id,
                "login": user_id,
                "title": data.get("fullname", user_id),
                "description": data.get("fullname", user_id),
                "email": data.get("email", ""),
                "pluginid": plugin_id,
            }
            for (user_id, data) in users
        ]

        return tuple(user_info)

    def updateUser(self, user_id, login_name):
        """Update the login name of the user with id user_id.

        This is a new part of the IUserEnumerationPlugin interface, but
        not interesting for us.
        """
        pass

    def updateEveryLoginName(self, quit_on_first_error=True):
        """Update login names of all users to their canonical value.

        This is a new part of the IUserEnumerationPlugin interface, but
        not interesting for us.
        """
        pass


InitializeClass(ZODBMutablePropertyProvider)


class PersistentProperties(PersistentMapping):
    pass
