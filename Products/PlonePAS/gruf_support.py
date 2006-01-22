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

$Id$
"""

import sys

from Products.PluggableAuthService.PluggableAuthService import \
          PluggableAuthService, _SWALLOWABLE_PLUGIN_EXCEPTIONS, LOG, BLATHER
#from Products.PluggableAuthService.PluggableAuthService import MANGLE_DELIMITER
from Products.PluggableAuthService.interfaces.plugins \
     import IRoleAssignerPlugin, IAuthenticationPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.plugins import IUserIntrospection

def authenticate(self, name, password, request):

    plugins = self.plugins

    try:
        authenticators = plugins.listPlugins(IAuthenticationPlugin)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        LOG('PluggableAuthService', BLATHER,
            'Plugin listing error',
            error=sys.exc_info())
        authenticators = ()

    credentials = {'login': name,
                   'password': password}

    user_id = None

    for authenticator_id, auth in authenticators:
        try:
            uid_and_name = auth.authenticateCredentials(credentials)

            if uid_and_name == (None,None):
                continue

            user_id, name = uid_and_name

        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            LOG('PluggableAuthService', BLATHER,
                'AuthenticationPlugin %s error' %
                authenticator_id, error=sys.exc_info())
            continue

    if not user_id:
        return

    return self._findUser(plugins, user_id, name, request)

PluggableAuthService.authenticate = authenticate
PluggableAuthService.authenticate__roles__ = ()


#################################
# compat code galore
def userSetGroups(self, id, groupnames):
    plugins = self.plugins

    try:
        groupmanagers = plugins.listPlugins(IGroupManagement)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        LOG('PluggableAuthService', BLATHER,
            'Plugin listing error',
            error=sys.exc_info())
        groupmanagers = ()

    for group in groupnames:
        for gm_id, gm in groupmanagers:
            try:
                if gm.addPrincipalToGroup(id, group):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                LOG('PluggableAuthService', BLATHER,
                    'AuthenticationPlugin %s error' %
                    gm_id, error=sys.exc_info())

PluggableAuthService.userSetGroups = userSetGroups

#################################
# monkies for the diehard introspection.. all these should die, imho - kt
def getUsers(self):
    return ()

def getUserIds(self):
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        LOG('PluggableAuthService', BLATHER,
            'Plugin listing error',
            error=sys.exc_info())
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserIds())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            LOG('PluggableAuthService', BLATHER,
                    'AuthenticationPlugin %s error' %
                    introspector_id, error=sys.exc_info())

    return results


def getUserNames(self):
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        LOG('PluggableAuthService', BLATHER,
            'Plugin listing error',
            error=sys.exc_info())
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserNames())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            LOG('PluggableAuthService', BLATHER,
                    'AuthenticationPlugin %s error' %
                    introspector_id, error=sys.exc_info())

    return results

PluggableAuthService.getUsers = getUsers
PluggableAuthService.getUserIds = getUserIds
PluggableAuthService.getUserNames = getUserNames


#################################
# give interested parties some apriori way of noticing pas is a user folder impl
PluggableAuthService.isAUserFolder = 1
