# -*- coding: utf-8 -*-
"""
Mutable Property Provider
"""
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.utils import safe_unicode
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin  # noqa
from Products.PluggableAuthService.plugins.ZODBMutablePropertiesManager import ZODBMutablePropertiesManager  # noqa
from ZODB.PersistentMapping import PersistentMapping
from zope.interface import implementer
import copy


def manage_addZODBMutablePropertyProvider(
    self,
    id,
    title='',
    RESPONSE=None,
    schema=None,
    **kw
):
    """
    Create an instance of a mutable property manager.
    """
    ob = ZODBMutablePropertyProvider(id, title, schema, **kw)
    self._setObject(ob.getId(), ob)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addZODBMutablePropertyProviderForm = DTMLFile(
    "../zmi/MutablePropertyProviderForm", globals())


def isStringType(data):
    return isinstance(data, str) or isinstance(data, unicode)


class PloneMutablePropertySchemaFactory(object):
    """factory for mutable property sheet schemas.
    """

    def __init__(self, plugin):
        self.plugin = plugin

    def schema(self, user):
        """returns a schema
        """
        isgroup = getattr(user, 'isGroup', lambda: None)()
        datatool = isgroup and "portal_groupdata" or "portal_memberdata"
        # if no schema is provided, use portal_memberdata properties
        schema = ()
        tool = getToolByName(self, datatool, None)
        # Don't fail badly if tool is not available.
        if tool is not None:
            schema = [(elt['id'], elt['type']) for elt in tool.propertyMap()]
        return schema

    def defaultvalues(self, user):
        """returns default values for schema
        """
        isgroup = getattr(user, 'isGroup', lambda: None)()
        datatool = isgroup and "portal_groupdata" or "portal_memberdata"
        defaultvalues = {}
        tool = getToolByName(self, datatool, None)
        # Don't fail badly if tool is not available.
        if tool is not None:
            # we rely on propertyMap and propertyItems mapping
            mdvalues = tool.propertyItems()
            for name, value in mdvalues:
                # For selection types the default value is the name of a
                # method which returns the possible values. There is no way
                # to set a default value for those types.
                ptype = tool.getPropertyType(name)
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


@implementer(IUserEnumerationPlugin)
class ZODBMutablePropertyProvider(ZODBMutablePropertiesManager):
    """Storage for mutable properties in the ZODB for users/groups.

    API sounds like it's only for users, but groups work as well.
    """

    meta_type = 'ZODB Mutable Property Provider'
    security = ClassSecurityInfo()

    @security.private
    def testMemberData(self, memberdata, criteria, exact_match=False):
        """Test if a memberdata matches the search criteria.
        """
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
    def enumerateUsers(self, id=None, login=None,
                       exact_match=False, **kw):
        """ See IUserEnumerationPlugin.
        """
        plugin_id = self.getId()

        # This plugin can't search for a user by id or login, because there is
        # no such keys in the storage (data dict in the comprehensive list)
        # If kw is empty or not, we continue the search.
        if id is not None or login is not None:
            return ()

        criteria = copy.copy(kw)

        users = [(user, data) for (user, data) in self._storage.items()
                 if self.testMemberData(data, criteria, exact_match) and
                 not data.get('isGroup', False)]

        user_info = [{'id': self.prefix + user_id,
                      'login': user_id,
                      'title': data.get('fullname', user_id),
                      'description': data.get('fullname', user_id),
                      'email': data.get('email', ''),
                      'pluginid': plugin_id} for (user_id, data) in users]

        return tuple(user_info)

    def updateUser(self, user_id, login_name):
        """ Update the login name of the user with id user_id.

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
