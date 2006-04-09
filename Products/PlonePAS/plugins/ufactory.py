##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
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
$Id$
"""

from AccessControl import ClassSecurityInfo
from AccessControl.PermissionRole import _what_not_even_god_should_do
from Globals import InitializeClass, DTMLFile

from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PluggableAuthService.interfaces.plugins import IUserFactoryPlugin
from Products.PluggableAuthService.interfaces.propertysheets import IPropertySheet
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin

from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.utils import unique


manage_addPloneUserFactoryForm = DTMLFile('../zmi/PloneUserFactoryForm',
                                          globals())

def manage_addPloneUserFactory(self, id, title='', RESPONSE=None):
    """
    Add a plone user factory
    """

    puf = PloneUserFactory(id, title)
    self._setObject(puf.getId(), puf)

    if RESPONSE is not None:
        return RESPONSE.redirect('manage_workspace')


class PloneUserFactory(BasePlugin):

    security = ClassSecurityInfo()
    meta_type = 'Plone User Factory'

    def __init__(self, id, title=''):
        self.id = id
        self.title = title or self.meta_type

    security.declarePrivate('createUser')
    def createUser(self, user_id, name):
        return PloneUser(user_id, name)

classImplements(PloneUserFactory,
                IUserFactoryPlugin)

InitializeClass(PloneUserFactory)


class PloneUser(PropertiedUser):

    security = ClassSecurityInfo()

    #################################
    # GRUF API
    _isGroup = False

    security.declarePublic('isGroup')
    def isGroup(self):
        """Return 1 if this user is a group abstraction"""
        return self._isGroup

    security.declarePublic('getName')
    def getName(self):
        """Get user's or group's name.
        This is the id. PAS doesn't do prefixes and such like GRUF.
        """
        return self.getId()

    security.declarePublic('getName')
    def getUserId(self):
        """Get user's or group's name.
        This is the id. PAS doesn't do prefixes and such like GRUF.
        """
        return self.getId()

    security.declarePublic('getGroupNames')
    def getGroupNames(self):
        """Return ids of this user's groups. GRUF compat."""
        return self.getGroups()

    security.declarePublic('getGroupIds')
    getGroupIds = getGroupNames

    #################################
    # acquisition aware
    security.declarePublic('getPropertysheet')
    def getPropertysheet(self, id):
        """ -> propertysheet (wrapped if supported)
        """
        sheet = self._propertysheets[id]
        try:
            return sheet.__of__(self)
        except AttributeError:
            return sheet

    security.declarePrivate('addPropertysheet')
    def addPropertysheet(self, id, data):
        """ -> add a prop sheet, given data which is either
        a property sheet or a raw mapping.
        """
        if IPropertySheet.providedBy(data):
            sheet = data
        else:
            sheet = UserPropertySheet(id, **data)

        if self._propertysheets.get(id) is not None:
            raise KeyError, 'Duplicate property sheet: %s' % id

        self._propertysheets[id] = sheet

    def _getPropertyPlugins(self):
        return self.acl_users.plugins.listPlugins(IPropertiesPlugin)

    security.declarePrivate('getOrderedPropertySheets')
    def getOrderedPropertySheets(self):
        source_provider_keys = [plugin_id for plugin_id, plugin in
                                self._getPropertyPlugins()]
        provider_keys = self.listPropertysheets()
        sheets = [self.getPropertysheet(pk) for pk in source_provider_keys
                  if pk in provider_keys]
        return sheets

    #################################
    # local roles plugin type delegation

    def _getLocalRolesPlugins(self):
        return self.acl_users.plugins.listPlugins(ILocalRolesPlugin)

    def getRolesInContext(self, object):
        lrmanagers = self._getLocalRolesPlugins()
        roles = []
        for lrid, lrmanager in lrmanagers:
            roles.extend(lrmanager.getRolesInContext(self, object))
        return unique(roles)

    def allowed(self, object, object_roles = None):
        if object_roles is _what_not_even_god_should_do:
            return 0

        # Short-circuit the common case of anonymous access.
        if object_roles is None or 'Anonymous' in object_roles:
            return 1

        # Provide short-cut access if object is protected by 'Authenticated'
        # role and user is not nobody
        if 'Authenticated' in object_roles and (
            self.getUserName() != 'Anonymous User'):
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

InitializeClass(PloneUser)
