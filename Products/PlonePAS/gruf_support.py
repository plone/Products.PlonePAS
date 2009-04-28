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
gruf specific hacks to pas, to make it play well in gruf

in general its not recommended, but its a low risk mechanism for
experimenting with pas flexibility on an existing system.

open question if this mode will be supported at all

"""

import logging
from zope.deprecation import deprecate
from sets import Set

from Products.PluggableAuthService.PluggableAuthService import security
from Products.PluggableAuthService.PluggableAuthService import \
          PluggableAuthService, _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.plugins \
     import IAuthenticationPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.plugins import IUserIntrospection

from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('Plone')

def authenticate(self, name, password, request):

    plugins = self.plugins

    try:
        authenticators = plugins.listPlugins(IAuthenticationPlugin)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        authenticators = ()

    credentials = {'login': name,
                   'password': password}

    user_id = None

    for authenticator_id, auth in authenticators:
        try:
            uid_and_name = auth.authenticateCredentials(credentials)
            if uid_and_name is not None:
                user_id, name = uid_and_name
                break
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info('PluggableAuthService: AuthenticationPlugin %s error',
                    authenticator_id, exc_info=1)
            continue

    if not user_id:
        return

    return self._findUser(plugins, user_id, name, request)

PluggableAuthService.authenticate = authenticate
PluggableAuthService.authenticate__roles__ = ()


#################################
# compat code galore
@deprecate("userSetGroups is deprecated. Use the PAS methods instead")
def userSetGroups(self, id, groupnames):
    plugins = self.plugins
    gtool = getToolByName(self, "portal_groups")

    member = self.getUser(id)
    groupnameset = Set(groupnames)

    # remove absent groups
    groups = Set(gtool.getGroupsForPrincipal(member))
    rmgroups = groups - groupnameset
    for gid in rmgroups:
        try:
            gtool.removePrincipalFromGroup(id, gid)
        except KeyError:
            # We could hit a group which does not allow user removal, such as
            # created by our AutoGroup plugin.
            pass

    # add groups
    try:
        groupmanagers = plugins.listPlugins(IGroupManagement)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        groupmanagers = ()

    for group in groupnames:
        for gm_id, gm in groupmanagers:
            try:
                if gm.addPrincipalToGroup(id, group):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                logger.info('PluggableAuthService: GroupManagement %s error',
                            gm_id, exc_info=1)

PluggableAuthService.userSetGroups = userSetGroups

@deprecate("userFolderAddGroup is deprecated. Use the PAS methods instead")
def userFolderAddGroup(self, name, roles, groups = (), **kw):
    gtool = getToolByName(self, 'portal_groups')
    return gtool.addGroup(name, roles, groups, **kw)

PluggableAuthService.userFolderAddGroup = userFolderAddGroup

#################################
# monkies for the diehard introspection.. all these should die, imho - kt

@deprecate("getUserIds is deprecated. Use the PAS methods instead")
def getUserIds(self):
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserIds())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info('PluggableAuthService: UserIntrospection %s error',
                    introspector_id, exc_info=1)

    return results


@deprecate("getUserNames is deprecated. Use the PAS methods instead")
def getUserNames(self):
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserNames())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info('PluggableAuthService: UserIntroSpection plugin %s error',
                    introspector_id, exc_info=1)

    return results

PluggableAuthService.getUserIds = getUserIds
PluggableAuthService.getUserNames = getUserNames

#################################
# Evil role aquisition blocking

# XXX: Is this used anywhere, all the code seems to use the PloneTool method
def acquireLocalRoles(self, obj, status = 1):
    """If status is 1, allow acquisition of local roles (regular behaviour).

    If it's 0, prohibit it (it will allow some kind of local role blacklisting).
    """
    # Set local role status
    if not status:
        obj.__ac_local_roles_block__ = 1
    else:
        if getattr(obj, '__ac_local_roles_block__', None):
            obj.__ac_local_roles_block__ = None

PluggableAuthService._acquireLocalRoles = acquireLocalRoles

#################################
# give interested parties some apriori way of noticing pas is a user folder impl
PluggableAuthService.isAUserFolder = 1

