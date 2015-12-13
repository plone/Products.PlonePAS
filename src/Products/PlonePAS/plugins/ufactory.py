# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from AccessControl.PermissionRole import _what_not_even_god_should_do
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserFactoryPlugin
from Products.PluggableAuthService.interfaces.propertysheets \
    import IPropertySheet
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.interface import implementer

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

manage_addPloneUserFactoryForm = DTMLFile('../zmi/PloneUserFactoryForm',
                                          globals())

_marker = object()


def manage_addPloneUserFactory(self, id, title='', RESPONSE=None):
    """
    Add a plone user factory
    """

    puf = PloneUserFactory(id, title)
    self._setObject(puf.getId(), puf)

    if RESPONSE is not None:
        return RESPONSE.redirect('manage_workspace')


@implementer(IUserFactoryPlugin)
class PloneUserFactory(BasePlugin):

    security = ClassSecurityInfo()
    meta_type = 'Plone User Factory'

    def __init__(self, id, title=''):
        self.id = id
        self.title = title or self.meta_type

    @security.private
    def createUser(self, user_id, name):
        return PloneUser(user_id, name)


InitializeClass(PloneUserFactory)


class PloneUser(PropertiedUser):

    security = ClassSecurityInfo()

    #################################
    # GRUF API
    _isGroup = False

    def __init__(self, id, login=None):
        super(PloneUser, self).__init__(id, login)
        self._propertysheets = OrderedDict()

    def _getPAS(self):
        # XXX This is not very optimal *at all*
        return self.acl_users

    def _getPlugins(self):
        # XXX This is not very optimal *at all*
        return self._getPAS().plugins

    @security.public
    def isGroup(self):
        """Return 1 if this user is a group abstraction"""
        return self._isGroup

    @security.public
    def getName(self):
        """Get user's or group's name.
        This is the id. PAS doesn't do prefixes and such like GRUF.
        """
        return self.getId()

    @security.public
    def getUserId(self):
        """Get user's or group's name.
        This is the id. PAS doesn't do prefixes and such like GRUF.
        """
        return self.getId()

    @security.public
    def getGroupNames(self):
        """Return ids of this user's groups. GRUF compat."""
        return self.getGroups()

    security.declarePublic('getGroupIds')
    getGroupIds = getGroupNames

    #################################
    # acquisition aware

    @security.public
    def getPropertysheet(self, id):
        """ -> propertysheet (wrapped if supported)
        """
        sheet = self._propertysheets[id]
        try:
            return sheet.__of__(self)
        except AttributeError:
            return sheet

    @security.private
    def addPropertysheet(self, id, data):
        """ -> add a prop sheet, given data which is either
        a property sheet or a raw mapping.
        """
        if IPropertySheet.providedBy(data):
            sheet = data
        else:
            sheet = UserPropertySheet(id, **data)

        if self._propertysheets.get(id) is not None:
            raise KeyError('Duplicate property sheet: %s' % id)

        self._propertysheets[id] = sheet

    def _getPropertyPlugins(self):
        return self._getPAS().plugins.listPlugins(IPropertiesPlugin)

    @security.private
    def getOrderedPropertySheets(self):
        return self._propertysheets.values()

    #################################
    # local roles plugin type delegation

    def _getLocalRolesPlugins(self):
        return self._getPAS().plugins.listPlugins(ILocalRolesPlugin)

    def getRolesInContext(self, object):
        lrmanagers = self._getLocalRolesPlugins()
        roles = set([])
        for lrid, lrmanager in lrmanagers:
            roles.update(lrmanager.getRolesInContext(self, object))
        roles.update(self.getRoles())
        return list(roles)

    def allowed(self, object, object_roles=None):
        if object_roles is _what_not_even_god_should_do:
            return 0

        # Short-circuit the common case of anonymous access.
        if object_roles is None or 'Anonymous' in object_roles:
            return 1

        # Provide short-cut access if object is protected by 'Authenticated'
        # role and user is not nobody
        if 'Authenticated' in object_roles \
           and self.getUserName() != 'Anonymous User':
            return 1

        # Check for ancient role data up front, convert if found.
        # This should almost never happen, and should probably be
        # deprecated at some point.
        if 'Shared' in object_roles:
            object_roles = self._shared_roles(object)
            if object_roles is None or 'Anonymous' in object_roles:
                return 1

        # Check for a role match with the normal roles given to
        # the user, then with local roles only if necessary. We
        # want to avoid as much overhead as possible.
        user_roles = self.getRoles()
        for role in object_roles:
            if role in user_roles:
                if self._check_context(object):
                    return 1
                return None

        # check for local roles
        lrmanagers = self._getLocalRolesPlugins()

        for lrid, lrm in lrmanagers:
            allowed = lrm.checkLocalRolesAllowed(self, object, object_roles)
            # return values
            # 0, 1, None
            # - 1 success
            # - 0 object context violation
            # - None - failure
            if allowed is None:
                continue
            return allowed
        return None

    def setProperties(self, properties=None, **kw):
        """ Set properties on a given user.

        Accepts either keyword arguments or a mapping for the ``properties``
        argument. The ``properties`` argument will take precedence over
        keyword arguments if both are provided; no merging will occur.
        """
        if properties is None:
            properties = kw

        for sheet in self.getOrderedPropertySheets():
            if not IMutablePropertySheet.providedBy(sheet):
                continue

            update = {}
            for (key, value) in properties.items():
                if sheet.hasProperty(key):
                    update[key] = value
                    del properties[key]

            if update:
                sheet.setProperties(self, update)

    def getProperty(self, id, default=_marker):
        for sheet in self.getOrderedPropertySheets():
            if sheet.hasProperty(id):
                value = sheet.getProperty(id)
                if isinstance(value, unicode):
                    # XXX Temporarily work around the fact that
                    # property sheets blindly store and return
                    # unicode. This is sub-optimal and should be
                    # dealed with at the property sheets level by
                    # using Zope's converters.
                    return value.encode('utf-8')
                return value

        return default

InitializeClass(PloneUser)
